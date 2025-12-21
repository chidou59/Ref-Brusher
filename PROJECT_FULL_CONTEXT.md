# 项目上下文文档
生成时间: 2025-12-21 11:48:26

> 注意：此文档包含项目的完整代码细节。请将此文件发送给 AI 助手以便进行代码修改。

## 1. 项目目录结构 (Project Tree)

```text
📂 Ref-Brusher/
│   .gitattributes
│   .gitignore
│   build_tool.py
│   config.py
│   desktop.ini
│   diagnose.py
│   import_tool.py
│   main.py
│   PROJECT_FULL_CONTEXT.md
│   Ref-Brusher.spec
│   requirements.txt
│   文献国标刷_v1.0.spec
│   📂 core/
│   │   verifier.py
│   │   __init__.py
│   📂 fig/
│   📂 logic/
│   │   cn_search_engine.py
│   │   __init__.py
│   📂 models/
│   │   citation_model.py
│   │   __init__.py
│   📂 services/
│   │   formatter.py
│   │   orchestrator.py
│   │   __init__.py
│   │   📂 api_engines/
│   │   │   base_engine.py
│   │   │   cnki.py
│   │   │   crossref.py
│   │   │   dblp.py
│   │   │   openalex_engine.py
│   │   │   semantic_scholar.py
│   │   │   __init__.py
│   📂 ui_framework/
│   │   base_chart.py
│   │   base_dialogs.py
│   │   base_splash.py
│   │   base_window.py
│   │   chart_styles.py
│   │   ui_styles.py
│   │   __init__.py
│   📂 views/
│   │   main_view.py
│   │   __init__.py
│   📂 workers/
│   │   query_thread.py
│   │   __init__.py
```

## 2. 文件详细内容 (File Contents)

### 📄 `build_tool.py`

```python:build_tool.py
# build_tool.py
# ==============================================================================
# 可用接口:
# - build_exe(): 核心打包函数，自动处理依赖、图标、图片并调用 PyInstaller
#   (新增功能：如果程序未关闭，会提示用户重试，而不是直接报错)
# ==============================================================================

import os
import sys
import subprocess
import shutil
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.path.basename(BASE_DIR)
MAIN_FILE = "main.py"
EXTRA_FILES = ["background.jpg"]

def build_exe():
    print(f"🚀 启动打包工具 [目录: {BASE_DIR}]")
    os.chdir(BASE_DIR)

    # 0. 清理旧的构建文件 (带重试机制)
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            print(f"🧹 正在清理 {folder} 文件夹...")
            while True:
                try:
                    shutil.rmtree(folder)
                    break  # 成功删除，跳出循环
                except PermissionError:
                    print(f"\n⚠️ 无法删除 {folder}，因为它可能正在被占用。")
                    print("👉 请检查是否还没关闭之前的程序？(Ref-Brusher.exe)")
                    user_input = input("❌ 请关闭程序后按回车键重试 (输入 n 退出): ")
                    if user_input.lower() == 'n':
                        print("🚫 打包已取消。")
                        return
                except Exception as e:
                    print(f"❌ 清理出错: {e}")
                    return

    # 1. 确保环境里有 PySide6 和 PyInstaller
    print("📦 检查并安装必要环境...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PySide6", "pyinstaller"])
    except subprocess.CalledProcessError:
        print("⚠️ 安装库时出现警告，尝试继续...")

    # 2. 自动识别图标
    icon_file = None
    for f in os.listdir(BASE_DIR):
        if f.lower().endswith(".ico"):
            icon_file = f
            print(f"🎨 找到图标: {icon_file}")
            break

    # 3. 选择模式
    print("\n1. 单文件模式 (Onefile) - 只有一个exe，清爽但启动稍慢")
    print("2. 文件夹模式 (Onedir)  - 一个文件夹，启动快但在文件夹里找exe")
    user_choice = input("请输入选项 [默认 1]: ").strip()
    mode_arg = "--onedir" if user_choice == "2" else "--onefile"

    # 4. 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--clean",
        mode_arg,
        f'--name={APP_NAME}',
        # 强制包含关键子模块，防止自动识别失败
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtCore"
    ]

    if icon_file:
        cmd.append(f'--icon={icon_file}')

    # 添加背景图等静态文件
    for f in EXTRA_FILES:
        if os.path.exists(f):
            # Windows 分号分隔格式：源文件;目标位置(.)
            cmd.append(f'--add-data={f};.')
            print(f"🖼️ 已关联资源: {f}")

    # 如果有 views 或 services 文件夹，PyInstaller 通常能自动识别，
    # 但如果是单纯的资源文件夹 assets，需要手动添加：
    if os.path.exists("assets"):
        cmd.append('--add-data=assets;assets')

    cmd.append(MAIN_FILE)

    print(f"\n🛠️ 正在执行打包，请稍候...")
    try:
        subprocess.check_call(cmd)
        print(f"\n✅ 打包完成！exe 文件在 dist 文件夹中。")
        os.startfile("dist")
    except Exception as e:
        print(f"❌ 打包失败: {e}")

if __name__ == "__main__":
    build_exe()
```

---

### 📄 `config.py`

```python:config.py
"""
文件路径: config.py
=========================================================
【可用接口说明】

# 常量直接导入使用
from config import USER_AGENT, SEARCH_PRIORITY, SourceConfig, MIN_REQUEST_INTERVAL

# 1. 爬虫伪装与安全
USER_AGENT: str       # 发送请求时必须带上的身份标识
MIN_REQUEST_INTERVAL: float # 两次请求之间的最小间隔(秒)，防封号关键

# 2. 搜索策略
SEARCH_PRIORITY: list # 定义了API的搜索顺序

# 3. 数据源配置类
SourceConfig.OPENALEX_ENABLED  # OpenAlex 开关 (必须为 True 才能测试成功)
SourceConfig.DBLP_ENABLED      # DBLP 开关
SourceConfig.PUBMED_ENABLED    # PubMed 开关
...
=========================================================
"""

import os

# === 1. 全局身份标识 (防封号第一步: 礼貌) ===
# 许多学术 API (OpenAlex, Crossref) 鼓励开发者提供真实邮箱进入 "Polite Pool"。
# 如果你是公开发布软件，建议让用户在第一次打开软件时填入自己的邮箱，
# 或者申请一个项目专用的公共联系邮箱。
APP_NAME = "RefFormatter/1.0"
CONTACT_EMAIL = "developer@example.com"  # TODO: 建议在发布前改为真实邮箱
USER_AGENT = f"{APP_NAME} (mailto:{CONTACT_EMAIL})"

# === 2. 网络请求与安全设置 (防封号第二步: 克制) ===
TIMEOUT = 15  # 单个请求超时时间 (秒)
MAX_RETRIES = 2  # 请求失败后的重试次数

# 【关键】请求冷却时间 (秒)
# 公开软件必须限制请求频率，避免用户 IP 被各大网站拉黑。
# 建议至少设置为 1.0 秒。
MIN_REQUEST_INTERVAL = 1.0

# 代理池配置 (可选)
# 如果你需要翻墙查外文，且电脑开了代理，可以在这里配置
# 例如: PROXIES = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
PROXIES = None


# === 3. 数据源配置 ===
class SourceConfig:
    """
    管理各个 API 数据源的开关。
    """

    # --- 英文/国际权威数据源 (API友好，封号风险低) ---

    # 【核心】OpenAlex: 极其全面，免费，强烈推荐 (请确保此项为 True)
    OPENALEX_ENABLED = True
    OPENALEX_API_URL = "https://api.openalex.org/works"

    # Crossref: 英文 DOI 官方，数据最准 (备用)
    CROSSREF_ENABLED = True
    CROSSREF_API_URL = "https://api.crossref.org/works"

    # Semantic Scholar: AI 驱动，质量高 (需注意每5分钟100次限制)
    S2_ENABLED = True
    S2_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    S2_API_KEY = None

    # DBLP: 计算机科学领域权威 (无需Key，非常安全)
    DBLP_ENABLED = True
    DBLP_API_URL = "https://dblp.org/search/publ/api"

    # PubMed: 医学/生物领域 (无需Key，非常安全)
    PUBMED_ENABLED = True
    PUBMED_API_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    # --- 中文/网页爬虫数据源 (风险较高，需谨慎) ---
    # 注意：如果你还没有编写这些引擎的代码，即使设置为 True 也不会生效，
    # 因为 Orchestrator 里还没有加载它们。

    CNKI_ENABLED = True
    WANFANG_ENABLED = True
    BAIDU_SCHOLAR_ENABLED = True


# === 4. 智能搜索策略 ===
# 建议顺序：先查 API 开放友好的，再查需要硬爬的。
SEARCH_PRIORITY = [
    "cnki",  # 中文优先
    "wanfang",  # 中文补充
    "openalex",  # 英文首选 (量大速度快)
    "dblp",  # 计算机首选
    "pubmed",  # 医学首选
    "semanticscholar",  # 英文高质量
    "crossref",  # 英文保底
    "baidu_scholar"  # 最后的补漏
]

# === 5. 格式化标准 ===
DEFAULT_STYLE = "gbt7714-2015"
```

---

### 📄 `desktop.ini`

```ini:desktop.ini
[.ShellClassInfo]
IconResource=C:\Users\hansh\PycharmProjects\Github\Ref-Brusher\Brush.ico,0
[ViewState]
Mode=
Vid=
FolderType=Generic

```

---

### 📄 `diagnose.py`

```python:diagnose.py
"""
文件路径: diagnose.py
=========================================================
【作用】
独立运行此脚本，诊断 API、配置和路径问题。
不依赖界面，直接在控制台输出结果。
=========================================================
"""
import sys
import os
import time

# 1. 强制设置路径，模拟 main.py 的环境
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=" * 50)
print(f"🚀 开始诊断 (RefFormatter Diagnostic)")
print(f"📂 当前工作目录: {os.getcwd()}")
print(f"🐍 Python 解释器: {sys.executable}")
print("=" * 50)

try:
    # 2. 检查 Config
    print("\n[1/4] 检查配置 (config.py)...")
    import config

    print(f"   -> 配置文件路径: {config.__file__}")
    print(f"   -> OpenAlex 开关: {config.SourceConfig.OPENALEX_ENABLED}")
    print(f"   -> MIN_REQUEST_INTERVAL: {config.MIN_REQUEST_INTERVAL}")

    if not config.SourceConfig.OPENALEX_ENABLED:
        print("   ❌ 警告: OpenAlex 未启用！请修改 config.py。")

    # 3. 检查 Orchestrator 文件来源
    print("\n[2/4] 检查核心逻辑 (Orchestrator)...")
    from services.orchestrator import Orchestrator
    import inspect

    orc_file = inspect.getfile(Orchestrator)
    print(f"   -> 代码加载自: {orc_file}")

    # 读取文件前几行，看看有没有我们写的 [调试] 字样
    with open(orc_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if "[调试]" in content:
            print("   ✅ 代码版本验证通过 (检测到调试代码)")
        else:
            print("   ❌ 警告: 加载的是旧版本代码！没有检测到 print 调试语句。")
            print("      请检查你是否保存了文件，或是否有重名文件。")

    # 4. 检查 API 引擎
    print("\n[3/4] 初始化引擎...")
    orc = Orchestrator()
    print(f"   -> 已加载引擎数量: {len(orc.engines)}")
    if len(orc.engines) > 0:
        print(f"   -> 第一个引擎是: {orc.engines[0].name}")
    else:
        print("   ❌ 错误: 引擎列表为空！")

    # 5. 实弹射击测试
    print("\n[4/4] 发起测试请求...")
    test_query = "Deep learning Nature 2015"
    print(f"   -> 测试词: '{test_query}'")

    # 强制刷新缓冲区，确保 print 出来
    sys.stdout.flush()

    result = orc.format_single(test_query)

    print("-" * 30)
    print(f"📝 最终返回结果:\n{result}")
    print("-" * 30)

    if "[J]" in result or "Nature" in result:
        print("\n✅ 诊断结论: 核心逻辑正常！问题可能出在 UI 或 线程调用上。")
    else:
        print("\n❌ 诊断结论: 核心逻辑返回了非标准格式，请检查网络或解析代码。")

except Exception as e:
    import traceback

    print("\n❌ 发生严重错误:")
    traceback.print_exc()

print("\n诊断结束。")
```

---

### 📄 `main.py`

```python:main.py
# main.py
# ==============================================================================
# 可用接口:
# - get_resource_path(relative_path): 获取打包后资源的绝对路径
# - RefFormatterController.run(): 启动 GUI 程序
# ==============================================================================

import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
from PySide6.QtCore import QThread, Signal, QObject, Qt

# 导入你自己的模块
from views.main_view import MainView
from services.orchestrator import Orchestrator


def get_resource_path(relative_path):
    """ 获取资源绝对路径，解决打包后找不到文件的问题 """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时解压路径
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境下的当前路径
    return os.path.join(os.path.abspath("."), relative_path)


# 预加载资源路径（供 views 或其他地方使用）
BG_PATH = get_resource_path("background.jpg")


class WorkerThread(QThread):
    progress_updated = Signal(int, str)
    result_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, orchestrator, raw_text):
        super().__init__()
        self.orchestrator = orchestrator
        self.raw_text = raw_text

    def run(self):
        try:
            def progress_callback(percent, message):
                self.progress_updated.emit(percent, message)

            final_result = self.orchestrator.format_batch(
                self.raw_text,
                callback_signal=progress_callback
            )
            self.result_ready.emit(final_result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class RefFormatterController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # 如果你的 MainView 需要背景图，可以把 BG_PATH 传进去
        self.view = MainView()
        self.view.setup_ui()
        self.orchestrator = Orchestrator()
        self.worker = None
        self.current_results = {"with_num": "", "no_num": ""}
        self.connect_signals()
        self.view.show()

    def connect_signals(self):
        if hasattr(self.view, 'btn_convert') and self.view.btn_convert:
            self.view.btn_convert.clicked.connect(self.start_batch_processing)
        if hasattr(self.view, 'btn_copy_with_num') and self.view.btn_copy_with_num:
            self.view.btn_copy_with_num.clicked.connect(self.copy_result_with_num)
        if hasattr(self.view, 'btn_copy_no_num') and self.view.btn_copy_no_num:
            self.view.btn_copy_no_num.clicked.connect(self.copy_result_no_num)

    def start_batch_processing(self):
        raw_text = self.view.get_input_text()
        if not raw_text.strip():
            self.view.status_label.setText("⚠️ 请先输入内容")
            return

        self.view.btn_convert.setEnabled(False)
        self.view.btn_convert.setText("⏳")
        self.view.btn_copy_with_num.setEnabled(False)
        self.view.btn_copy_no_num.setEnabled(False)
        self.view.status_label.setText("🚀 启动中...")
        self.view.set_output_text("")  # 清空
        self.view.last_result_label.setText("")

        self.worker = WorkerThread(self.orchestrator, raw_text)
        self.worker.progress_updated.connect(self.on_progress)
        self.worker.result_ready.connect(self.on_finished)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()

    def on_progress(self, percent, message):
        if "|" in message:
            status, real_msg = message.split("|", 1)
            self.view.status_label.setText(f"⏳ {real_msg} ({percent}%)")

            if status == "PREV_OK":
                self.view.last_result_label.setText("✅ 上一条：修改成功")
                self.view.last_result_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            elif status == "PREV_FAIL":
                self.view.last_result_label.setText("❌ 上一条：未找到/失败")
                self.view.last_result_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        else:
            self.view.status_label.setText(f"⏳ {message} ({percent}%)")

        if self.view.btn_convert:
            self.view.btn_convert.setText(f"{percent}%")

    def on_finished(self, result_dict):
        self.current_results = result_dict

        # 【关键修改】使用 HTML 渲染，支持点击跳转
        if "display_html" in result_dict:
            self.view.set_output_html(result_dict["display_html"])
        else:
            # 兼容旧逻辑
            self.view.set_output_text(result_dict["with_num"])

        self.view.status_label.setText("✅ 全部处理完毕")
        self.view.last_result_label.setText("")

        self.view.btn_convert.setEnabled(True)
        self.view.btn_convert.setText("格式化 \n >>>")
        self.view.btn_copy_with_num.setEnabled(True)
        self.view.btn_copy_no_num.setEnabled(True)
        self.worker = None

    def on_error(self, error_msg):
        self.view.status_label.setText(f"❌ 错误: {error_msg}")
        self.view.output_edit.setPlainText(f"出错: {error_msg}")
        self.view.btn_convert.setEnabled(True)
        self.view.btn_convert.setText("重试")
        self.worker = None

    def copy_result_with_num(self):
        # 复制时依然使用纯文本
        text = self.current_results.get("with_num", "")
        if text:
            clean_text = text.replace("\n\n", "\n")
            QApplication.clipboard().setText(clean_text)
            self.view.status_label.setText("📋 已复制 (带序号)")

    def copy_result_no_num(self):
        text = self.current_results.get("no_num", "")
        if text:
            clean_text = text.replace("\n\n", "\n")
            QApplication.clipboard().setText(clean_text)
            self.view.status_label.setText("📋 已复制 (纯净版)")

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    controller = RefFormatterController()
    controller.run()
```

---

### 📄 `core\verifier.py`

```python:core\verifier.py
# --------------------------------------------------------------------------------
# 文件功能：参考文献格式复核器 (Verifier)
# --------------------------------------------------------------------------------
#
# 【可用的接口 (Public Methods)】
# 供 main.py 调用：
#
# class ReferenceVerifier:
#    - verify(text: str) -> dict:
#         检查单条文献格式。
#         返回一个字典，包含:
#         {
#             "is_valid": bool,   # 是否通过复核
#             "reason": str       # 如果失败，具体的错误原因 (例如 "缺少年份")
#         }
#
# --------------------------------------------------------------------------------

import re

class ReferenceVerifier:
    """
    专门用于检查参考文献格式是否符合 GB/T 7714 标准的工具类
    """

    def verify(self, text: str) -> dict:
        """
        核心复核方法
        :param text: 待检查的文献文本
        :return: 包含检查结果和原因的字典
        """
        text = text.strip()
        result = {
            "is_valid": True,
            "reason": "格式规范"
        }

        # 规则 1: 检查结尾标点
        # 国标规定结尾必须是点号 "."
        if not text.endswith("."):
            result["is_valid"] = False
            result["reason"] = "缺少结尾点号(.)"
            return result

        # 规则 2: 检查年份
        # 必须包含 19xx 或 20xx 的年份格式
        if not re.search(r'(19|20)\d{2}', text):
            result["is_valid"] = False
            result["reason"] = "未检测到有效年份"
            return result

        # 规则 3: 检查长度 (防止空结果或过短的错误结果)
        if len(text) < 10:
            result["is_valid"] = False
            result["reason"] = "内容过短，可能不是有效文献"
            return result

        # 如果通过所有规则
        return result
```

---

### 📄 `core\__init__.py`

```python:core\__init__.py

```

---

### 📄 `logic\cn_search_engine.py`

```python:logic\cn_search_engine.py
# logic/cn_search_engine.py
# ==============================================================================
# 模块名称: 中文文献搜索引擎 (Based on Baidu Scholar)
# 功能描述: 模拟浏览器访问百度学术，抓取搜索结果的第一条匹配项。
#
# 可用接口 (Public Interfaces):
# 1. engine = BaiduScholarEngine()
#    - 初始化引擎。
#
# 2. result = engine.search(keyword)
#    - 输入: keyword (str) - 论文标题或关键词
#    - 输出: dict (字典) 或 None
#      成功时返回字典格式:
#      {
#          'title': '论文标题',
#          'author': '作者1, 作者2',
#          'year': '2023',
#          'journal': '期刊名称',
#          'url': '百度学术链接',
#          'type': 'CN'  # 标识为中文来源
#      }
#      失败或未找到时返回: None
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import time
import random


class BaiduScholarEngine:
    """
    百度学术搜索引擎封装类
    """

    def __init__(self):
        # 基础搜索链接
        self.base_url = "https://xueshu.baidu.com/s"
        # 请求头 (User-Agent): 伪装成正常的浏览器，防止被百度拦截
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }

    def search(self, keyword):
        """
        核心搜索方法
        :param keyword: 搜索关键词 (通常是论文标题)
        :return: 包含文献信息的字典，如果失败则返回 None
        """
        if not keyword or not keyword.strip():
            return None

        # 构造查询参数
        params = {
            'wd': keyword,  # 搜索词
            'tn': 'SE_baiduxueshu_c1gjeupa',  # 百度学术特定的来源标识
            'ie': 'utf-8',  # 编码
            'sc_hit': '1'  # 命中策略
        }

        try:
            # 1. 发起网络请求
            # timeout=10 表示如果10秒没反应就报错，避免程序卡死
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'  # 强制使用utf-8编码，防止中文乱码

            if response.status_code != 200:
                print(f"[CN_Search] 请求失败，状态码: {response.status_code}")
                return None

            # 2. 解析网页 (使用 BeautifulSoup)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 3. 提取第一条结果
            # 百度学术的搜索结果列表通常在 div class="sc_content" 中
            # 我们只取第一个结果 (find 方法只找第一个)
            first_result = soup.find('div', class_='sc_content')

            if not first_result:
                print(f"[CN_Search] 未找到关于 '{keyword}' 的中文结果。")
                return None

            # --- 开始提取具体字段 ---

            # (A) 标题
            # 通常在 h3 标签下的 a 标签里
            title_tag = first_result.find('h3', class_='t')
            if title_tag and title_tag.find('a'):
                raw_title = title_tag.find('a').get_text(strip=True)
                # 百度有时候会在标题里加 <em> 标签标红关键词，get_text 会自动去掉标签只留文字
                title = raw_title
                link = title_tag.find('a')['href']
            else:
                title = "未知标题"
                link = ""

            # (B) 作者、年份、期刊
            # 这些信息通常混杂在 class="sc_info" 的 div 里
            info_div = first_result.find('div', class_='sc_info')

            author_str = ""
            year_str = ""
            journal_str = ""

            if info_div:
                # 1. 提取作者 (作者通常包含在 data-click 属性或者直接是 a 标签)
                # 简单策略：提取 sc_info 下所有的 a 标签，只要不是链接到期刊的，通常就是作者
                # 百度学术结构：作者1, 作者2 - 期刊名 - 年份

                # 获取该行所有文本内容，然后手动分割可能更稳妥
                # 例子: "张三, 李四 - 计算机学报 - 2023 - 被引量: 5"
                info_text = info_div.get_text(" ", strip=True)  # 用空格连接

                # 尝试分离年份 (通常是4位数字)
                # 这是一个简单的查找策略，找文本中出现的年份
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', info_text)
                if year_match:
                    year_str = year_match.group(0)

                # 尝试分离作者 (通常在第一个破折号 - 之前)
                # 这里为了准确，我们还是解析 HTML 标签
                author_links = info_div.find_all('a')
                if author_links:
                    # 假设前2个链接是作者 (根据经验)
                    # 过滤掉不需要的链接（比如 DOI 跳转链接）
                    valid_authors = []
                    for al in author_links:
                        # 简单的过滤逻辑：作者名字通常比较短
                        name = al.get_text(strip=True)
                        if len(name) < 10 and not name.isdigit():
                            valid_authors.append(name)

                    author_str = ", ".join(valid_authors[:3])  # 只取前3个

                # 尝试分离期刊 (通常在 sc_journal 样式里，或者在作者和年份中间)
                journal_tag = info_div.find('span', class_='sc_journal')
                if journal_tag:
                    journal_str = journal_tag.get_text(strip=True)
                else:
                    # 如果没有专门标签，尝试用 sc_info 的文本分析
                    # 这是一个保底策略，未必100%准确，但够用
                    parts = info_text.split('-')
                    if len(parts) >= 2:
                        # 假设中间一段是期刊
                        potential_journal = parts[1].strip()
                        # 如果这段不是年份，就当它是期刊
                        if not potential_journal.isdigit():
                            journal_str = potential_journal

            # 4. 组装结果
            result_data = {
                'title': title,
                'author': author_str if author_str else "未知作者",
                'year': year_str if year_str else "",
                'journal': journal_str if journal_str else "网络文献/未知来源",
                'url': link,
                'type': 'CN'  # 标记为中文
            }

            # 5. 随机等待 (礼貌爬虫)
            # 避免请求太快被百度封IP，随机等待 0.5 到 1.5 秒
            time.sleep(random.uniform(0.5, 1.5))

            return result_data

        except requests.Timeout:
            print("[CN_Search] 网络请求超时。请检查网络连接。")
            return None
        except Exception as e:
            print(f"[CN_Search] 发生未知错误: {e}")
            return None


# ==============================================================================
# 自我测试模块
# 当你直接运行这个文件时 (python logic/cn_search_engine.py)，下面的代码会执行。
# 当此文件被其他文件 import 时，下面的代码不会执行。
# ==============================================================================
if __name__ == "__main__":
    print("正在测试中文搜索引擎...")

    # 1. 实例化
    engine = BaiduScholarEngine()

    # 2. 定义测试关键词
    test_keyword = "深度学习在图像识别中的应用"
    print(f"正在搜索: {test_keyword} ...")

    # 3. 执行搜索
    result = engine.search(test_keyword)

    # 4. 打印结果
    if result:
        print("\n✅ 搜索成功!")
        print("-" * 30)
        print(f"标题: {result['title']}")
        print(f"作者: {result['author']}")
        print(f"年份: {result['year']}")
        print(f"期刊: {result['journal']}")
        print(f"链接: {result['url']}")
        print("-" * 30)
    else:
        print("\n❌ 搜索失败或未找到结果。")
```

---

### 📄 `logic\__init__.py`

```python:logic\__init__.py

```

---

### 📄 `models\citation_model.py`

```python:models\citation_model.py
"""
文件路径: models/citation_model.py
=========================================================
【可用接口说明】

class CitationData:
    # --- 核心属性 (直接访问/赋值) ---
    title: str       # 标题
    authors: list    # 作者列表，如 ["张三", "Li Si"]
    source: str      # 来源 (期刊名/会议名/出版社)
    year: str        # 年份 (如 "2023")
    volume: str      # 卷
    issue: str       # 期
    pages: str       # 页码
    doi: str         # DOI号
    url: str         # 链接
    entry_type: str  # 类型 ("article", "book", "thesis", "conference")

    # --- 常用方法 ---
    def is_valid(self) -> bool:
        '''
        检查数据是否基本完整。
        返回: True (完整) / False (缺关键信息)
        '''
        pass

    def get_formatted_authors(self, max_authors=3) -> str:
        '''
        获取格式化后的作者字符串。
        参数: max_authors (超过多少人显示"等")
        返回: 如 "张三, 李四, 等"
        '''
        pass
=========================================================
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class CitationData:
    """
    统一的文献数据模型。
    作用：无论从哪个网站(OpenAlex/CNKI)抓取的数据，
    都必须先转换成这个类，然后再进行格式化。
    """
    # 核心字段
    title: str = ""
    authors: List[str] = field(default_factory=list)  # 注意：这是列表，不是字符串
    source: str = ""  # 期刊名、会议名或出版社
    year: str = ""

    # 详细字段
    volume: str = ""  # 卷
    issue: str = ""  # 期
    pages: str = ""  # 页码 (起止页)
    doi: str = ""  # Digital Object Identifier (数字对象唯一标识符)
    url: str = ""  # 链接

    # 元数据
    entry_type: str = "article"  # 默认为期刊论文，可选 book, thesis, conference
    raw_data: dict = field(default_factory=dict)  # 保留原始API返回的数据，以此备查

    def is_valid(self) -> bool:
        """
        判断数据是否基本完整。
        标准：至少要有 标题、作者、来源、年份。
        如果返回 False，UI 上可以用红色高亮显示，提示用户补全。
        """
        # 使用 all() 检查核心字段是否都有值
        required_fields = [self.title, self.authors, self.source, self.year]
        return all(required_fields)

    def get_formatted_authors(self, max_authors=3) -> str:
        """
        根据国标逻辑简单处理作者名单。
        注：更复杂的逻辑（如英文姓在前名在后）会在 formatter 服务中处理，
        这里提供的是用于 UI 预览的基础文本。
        """
        if not self.authors:
            return "[佚名]"

        # 1. 清理数据：移除可能的空字符串和多余空格
        cleaned_authors = [str(a).strip() for a in self.authors if str(a).strip()]

        if not cleaned_authors:
            return "[佚名]"

        # 2. 判断是否超过限制
        if len(cleaned_authors) <= max_authors:
            # 不超过3人，全部列出
            return ", ".join(cleaned_authors)
        else:
            # 超过3人，列出前3个 + ", 等" (英文环境可能需要变成 ", et al.")
            # 这里的本地化处理将在 formatter 中完善，此处暂用中文
            return ", ".join(cleaned_authors[:max_authors]) + ", 等"

    def __repr__(self):
        """控制台打印时的显示格式，方便调试查看"""
        author_preview = self.authors[0] if self.authors else "No Author"
        return f"<Citation: {self.title[:20]}... | {author_preview} ({self.year})>"
```

---

### 📄 `models\__init__.py`

```python:models\__init__.py

```

---

### 📄 `services\formatter.py`

```python:services\formatter.py
"""
文件路径: services/formatter.py
=========================================================
【功能】
将 CitationData 对象转换为标准的 GB/T 7714-2015 字符串。
遵循最严格的国标规定：
1. 姓氏全部大写 (EINSTEIN)
2. 名字首字母大写，无缩写点 (A)
3. 支持 van, von 等复姓识别
4. 【精准版】支持中国学者拼音双名自动拆分 (Han Shaoheng -> HAN S H)
   - 引入拼音字典校验，防止误伤外国名字 (如 Simona 不会被拆)
=========================================================
"""

import re
import html
from models.citation_model import CitationData

# === 1. 数据准备 ===

# 常见中国姓氏拼音 (大写)，用于触发检查
# 包含百家姓 Top 200+，覆盖率极高，防止对纯老外名字触发拼音检测
COMMON_CN_SURNAMES = {
    "LI", "WANG", "ZHANG", "LIU", "CHEN", "YANG", "ZHAO", "HUANG", "ZHOU", "WU",
    "XU", "SUN", "HU", "ZHU", "GAO", "LIN", "HE", "GUO", "MA", "LUO",
    "LIANG", "SONG", "ZHENG", "XIE", "HAN", "TANG", "FENG", "YU", "DONG", "XIAO",
    "CHENG", "CAO", "YUAN", "DENG", "FU", "SHEN", "ZENG", "PENG", "LV",
    "SU", "LU", "JIANG", "CAI", "JIA", "DING", "WEI", "XUE", "YE", "YAN",
    "PAN", "DU", "DAI", "XIA", "ZHONG", "TIAN", "REN", "FAN", "FANG", "SHI",
    "YAO", "TAN", "SHENG", "ZOU", "XIONG", "JIN", "HAO", "KONG", "BAI", "CUI",
    "KANG", "MAO", "QIU", "QIN", "GU", "HOU", "SHAO", "MENG", "LONG", "WAN",
    "DUAN", "QIAN", "YIN", "YI", "CHANG", "XI", "WEN", "NIE", "ZHUANG", "YAN",
    "QU", "GE", "PU", "BA", "BIE", "BING", "BO", "BU", "CEN", "CHAI", "CHE",
    "CHI", "CHU", "CHUAN", "CHUN", "CONG", "CUO", "DA", "DAN", "DAO", "DI",
    "DIAN", "DIAO", "DIE", "DOU", "DU", "DUN", "E", "EN", "ER", "FA", "FEI",
    "FO", "FOU", "GAI", "GAN", "GANG", "GEN", "GENG", "GONG", "GOU", "GUAN",
    "GUI", "GUN", "HAI", "HANG", "HEI", "HEN", "HENG", "HONG", "HUA", "HUAI",
    "HUAN", "HUI", "HUN", "HUO", "JI", "JIAN", "JIANG", "JIAO", "JIE", "JING",
    "JIONG", "JIU", "JU", "JUAN", "JUE", "JUN", "KA", "KAI", "KAN", "KAO", "KE",
    "KEN", "KENG", "KOU", "KU", "KUA", "KUAI", "KUAN", "KUANG", "KUI", "KUN",
    "KUO", "LA", "LAI", "LAN", "LANG", "LAO", "LE", "LEI", "LENG", "LIA", "LIAN",
    "LIAO", "LIE", "LIN", "LING", "LIU", "LONG", "LOU", "LUAN", "LUE", "LUN",
    "LUO", "MEI", "MEN", "MENG", "MI", "MIAN", "MIAO", "MIE", "MIN", "MING", "MIU",
    "MO", "MOU", "MU", "NA", "NAI", "NAN", "NANG", "NAO", "NE", "NEI", "NEN",
    "NENG", "NI", "NIAN", "NIANG", "NIAO", "NIE", "NIN", "NING", "NIU", "NONG",
    "NOU", "NU", "NUAN", "NUE", "NUO", "OU", "PA", "PAI", "PAN", "PANG", "PAO",
    "PEI", "PEN", "PENG", "PI", "PIAN", "PIAO", "PIE", "PIN", "PING", "PO", "POU",
    "QI", "QIA", "QIAN", "QIANG", "QIAO", "QIE", "QIN", "QING", "QIONG", "QIU",
    "QU", "QUAN", "QUE", "QUN", "RAN", "RANG", "RAO", "RE", "REN", "RENG", "RI",
    "RONG", "ROU", "RU", "RUAN", "RUI", "RUN", "RUO", "SA", "SAI", "SAN", "SANG",
    "SAO", "SE", "SEN", "SENG", "SHA", "SHAI", "SHAN", "SHANG", "SHE", "SHEI",
    "SHEN", "SHU", "SHUA", "SHUAI", "SHUAN", "SHUANG", "SHUI", "SHUN", "SHUO",
    "SI", "SONG", "SOU", "SUAN", "SUI", "SUN", "SUO", "TA", "TAI", "TAN", "TANG",
    "TAO", "TE", "TENG", "TI", "TIAN", "TIAO", "TIE", "TING", "TONG", "TOU", "TU",
    "TUAN", "TUI", "TUN", "TUO", "WA", "WAI", "WAN", "WANG", "WEI", "WEN", "WENG",
    "WO", "WU", "XI", "XIA", "XIAN", "XIANG", "XIAO", "XIE", "XIN", "XING", "XIONG",
    "XIU", "XU", "XUAN", "XUE", "XUN", "YA", "YAN", "YANG", "YAO", "YE", "YI",
    "YIN", "YING", "YONG", "YOU", "YU", "YUAN", "YUE", "YUN", "ZA", "ZAI", "ZAN",
    "ZANG", "ZAO", "ZE", "ZEI", "ZEN", "ZENG", "ZHA", "ZHAI", "ZHAN", "ZHANG",
    "ZHAO", "ZHE", "ZHEI", "ZHEN", "ZHENG", "ZHI", "ZHONG", "ZHOU", "ZHU", "ZHUA",
    "ZHUAI", "ZHUAN", "ZHUANG", "ZHUI", "ZHUN", "ZHUO", "ZI", "ZONG", "ZOU", "ZU",
    "ZUAN", "ZUI", "ZUN", "ZUO"
}

# 全量合法拼音音节表 (无声调)
# 来源：标准汉语拼音方案
VALID_PINYINS = {
    "a", "ai", "an", "ang", "ao", "ba", "bai", "ban", "bang", "bao", "bei", "ben",
    "beng", "bi", "bian", "biao", "bie", "bin", "bing", "bo", "bu", "ca", "cai",
    "can", "cang", "cao", "ce", "cen", "ceng", "cha", "chai", "chan", "chang",
    "chao", "che", "chen", "cheng", "chi", "chong", "chou", "chu", "chua", "chuai",
    "chuan", "chuang", "chui", "chun", "chuo", "ci", "cong", "cou", "cu", "cuan",
    "cui", "cun", "cuo", "da", "dai", "dan", "dang", "dao", "de", "dei", "deng",
    "di", "dian", "diao", "die", "ding", "diu", "dong", "dou", "du", "duan", "dui",
    "dun", "duo", "e", "ei", "en", "eng", "er", "fa", "fan", "fang", "fei", "fen",
    "feng", "fo", "fou", "fu", "ga", "gai", "gan", "gang", "gao", "ge", "gei",
    "gen", "geng", "gong", "gou", "gu", "gua", "guai", "guan", "guang", "gui",
    "gun", "guo", "ha", "hai", "han", "hang", "hao", "he", "hei", "hen", "heng",
    "hong", "hou", "hu", "hua", "huai", "huan", "huang", "hui", "hun", "huo", "ji",
    "jia", "jian", "jiang", "jiao", "jie", "jin", "jing", "jiong", "jiu", "ju",
    "juan", "jue", "jun", "ka", "kai", "kan", "kang", "kao", "ke", "ken", "keng",
    "kong", "kou", "ku", "kua", "kuai", "kuan", "kuang", "kui", "kun", "kuo", "la",
    "lai", "lan", "lang", "lao", "le", "lei", "leng", "li", "lia", "lian", "liang",
    "liao", "lie", "lin", "ling", "liu", "long", "lou", "lu", "luan", "lue", "lun",
    "luo", "lv", "ma", "mai", "man", "mang", "mao", "me", "mei", "men", "meng",
    "mi", "mian", "miao", "mie", "min", "ming", "miu", "mo", "mou", "mu", "na",
    "nai", "nan", "nang", "nao", "ne", "nei", "nen", "neng", "ni", "nian", "niang",
    "niao", "nie", "nin", "ning", "niu", "nong", "nou", "nu", "nuan", "nue", "nuo",
    "nv", "o", "ou", "pa", "pai", "pan", "pang", "pao", "pei", "pen", "peng", "pi",
    "pian", "piao", "pie", "pin", "ping", "po", "pou", "pu", "qi", "qia", "qian",
    "qiang", "qiao", "qie", "qin", "qing", "qiong", "qiu", "qu", "quan", "que",
    "qun", "ran", "rang", "rao", "re", "ren", "reng", "ri", "rong", "rou", "ru",
    "ruan", "rui", "run", "ruo", "sa", "sai", "san", "sang", "sao", "se", "sen",
    "seng", "sha", "shai", "shan", "shang", "shao", "she", "shei", "shen", "sheng",
    "shi", "shou", "shu", "shua", "shuai", "shuan", "shuang", "shui", "shun",
    "shuo", "si", "song", "sou", "su", "suan", "sui", "sun", "suo", "ta", "tai",
    "tan", "tang", "tao", "te", "teng", "ti", "tian", "tiao", "tie", "ting",
    "tong", "tou", "tu", "tuan", "tui", "tun", "tuo", "wa", "wai", "wan", "wang",
    "wei", "wen", "weng", "wo", "wu", "xi", "xia", "xian", "xiang", "xiao", "xie",
    "xin", "xing", "xiong", "xiu", "xu", "xuan", "xue", "xun", "ya", "yan", "yang",
    "yao", "ye", "yi", "yin", "ying", "yong", "you", "yu", "yuan", "yue", "yun",
    "za", "zai", "zan", "zang", "zao", "ze", "zei", "zen", "zeng", "zha", "zhai",
    "zhan", "zhang", "zhao", "zhe", "zhei", "zhen", "zheng", "zhi", "zhong",
    "zhou", "zhu", "zhua", "zhuai", "zhuan", "zhuang", "zhui", "zhun", "zhuo",
    "zi", "zong", "zou", "zu", "zuan", "zui", "zun", "zuo"
}


def clean_text(text: str) -> str:
    """清洗 HTML 标签"""
    if not text:
        return ""
    clean_str = re.sub(r'<[^>]+>', '', text)
    clean_str = html.unescape(clean_str)
    return clean_str.strip()


def try_split_pinyin(given_name: str) -> str:
    """
    【智能拼音拆分 - 严格校验版】
    尝试将连写的拼音双名拆开。
    策略：
    1. 遍历所有可能的分割点。
    2. 只有当拆分出的【两部分】都在 VALID_PINYINS 字典中时，才视为有效拆分。
    3. 防止将 "Simona" 误拆为 "Si mona" (mona 不是拼音)。
    """
    given_name = given_name.strip()
    length = len(given_name)

    # 拼音音节最短2字母(除了a,o,e)，最长6字母(zhuang)。
    # 双名总长度至少4 (如 bo yi)，通常不超过12。
    if length < 3 or length > 12:
        return given_name

    # 尝试从第2个字符到倒数第2个字符进行切分
    # 例如 "Shaoheng" (len 8)
    # i=2: Sh, aoheng (No)
    # i=4: Shao, heng (Yes!)

    # 优先寻找最合理的切分。
    # 从前往后切
    for i in range(1, length):
        part1 = given_name[:i].lower()
        part2 = given_name[i:].lower()

        # 核心校验：两部分必须都是合法拼音
        if part1 in VALID_PINYINS and part2 in VALID_PINYINS:
            # 找到合法拆分！直接返回
            return f"{given_name[:i]} {given_name[i:]}"

    # 如果找不到合法拆分，保持原样
    return given_name


def format_western_name(name_str: str) -> str:
    """
    【姓名整形师 V5.0】
    将外文姓名转换为 GB/T 7714 格式 (严格全大写)
    输入: "Ludwig van Beethoven" -> 输出: "VAN BEETHOVEN L"
    输入: "Han Shaoheng"         -> 输出: "HAN S H"
    输入: "Lee Simona"           -> 输出: "LEE S" (Simona 不是双名，不拆)
    """
    name_str = clean_text(name_str)
    if not name_str:
        return ""

    # 中文名直接返回 (简单判定)
    if re.search(r'[\u4e00-\u9fff]', name_str):
        return name_str

    # 定义常见的姓氏前缀 (小写)
    surname_prefixes = ['van', 'von', 'de', 'du', 'da', 'del', 'la', 'le']

    family = ""
    given = ""

    # 情况 A: 已经有逗号 "Beethoven, Ludwig van"
    if ',' in name_str:
        parts = name_str.split(',', 1)
        family = parts[0].strip()
        given = parts[1].strip()

    # 情况 B: 自然序 "Ludwig van Beethoven"
    else:
        tokens = name_str.split()
        if not tokens: return ""
        if len(tokens) == 1: return tokens[0].upper()

        # 智能检测复姓 (查看倒数第二个词是否是前缀)
        if len(tokens) > 2 and tokens[-2].lower() in surname_prefixes:
            # 姓是最后两个词: "van Beethoven"
            family = " ".join(tokens[-2:])
            given = " ".join(tokens[:-2])
        else:
            # 默认最后一个词是姓
            family = tokens[-1]
            given = " ".join(tokens[:-1])

    # === 核心国标规则 ===
    # 1. 姓: 全大写
    family_fmt = family.upper()

    # 2. 名: 处理逻辑
    # 【新增】针对中国学者拼音双名连写的特殊优化
    # 条件：姓氏是常见中国姓，且名字没有空格/连字符
    if family_fmt in COMMON_CN_SURNAMES and ' ' not in given and '-' not in given:
        given = try_split_pinyin(given)

    # 清理分隔符，统一变空格 (处理 Jean-Pierre -> Jean Pierre)
    given_clean = given.replace('.', ' ').replace('-', ' ')
    given_tokens = given_clean.split()

    # 提取首字母
    given_initials = [t[0].upper() for t in given_tokens if t]
    given_fmt = " ".join(given_initials)

    if given_fmt:
        return f"{family_fmt} {given_fmt}"
    else:
        return family_fmt


def format_authors(authors: list) -> str:
    """格式化作者列表"""
    if not authors:
        return "[佚名]"

    formatted_authors = []
    for auth in authors:
        fmt_name = format_western_name(auth)
        formatted_authors.append(fmt_name)

    # 前3位列出，超过3位加 et al.
    if len(formatted_authors) > 3:
        return ", ".join(formatted_authors[:3]) + ", et al"
    else:
        return ", ".join(formatted_authors)


def to_gbt7714(data: CitationData) -> str:
    """转换为国标字符串"""
    title = clean_text(data.title)
    source = clean_text(data.source)
    authors_str = format_authors(data.authors)

    doc_type = "[J]"
    if source:
        lower_source = source.lower()
        if "conference" in lower_source or "proceedings" in lower_source:
            doc_type = "[C]"
        elif "thesis" in lower_source or "dissertation" in lower_source:
            doc_type = "[D]"

    # 拼装
    result = f"{authors_str}. {title}{doc_type}"

    if source: result += f". {source}"
    if data.year: result += f", {data.year}"

    if data.volume:
        result += f", {data.volume}"
        if data.issue: result += f"({data.issue})"
    elif data.issue:
        result += f"({data.issue})"

    if data.pages:
        clean_pages = data.pages.replace("--", "-")
        result += f": {clean_pages}"

    result += "."
    return result


# ==============================================================================
# 自查测试模块 (Run this file to verify)
# ==============================================================================
if __name__ == "__main__":
    print("🚀 开始自查测试 (Formatter Self-Check)...\n")

    test_cases = [
        # --- 组1: 标准中国双名 (连写) ---
        ("Han Shaoheng", "HAN S H", "双名连写 - 基础"),
        ("Li Xiaolong", "LI X L", "双名连写 - Xiao"),
        ("Zhang Ziyi", "ZHANG Z Y", "双名连写 - Zi yi"),
        ("Wang Jingwei", "WANG J W", "双名连写 - Jing wei"),
        ("Chen Guangkun", "CHEN G K", "双名连写 - Guang kun"),

        # --- 组2: 中国单名 (不应拆) ---
        ("Wang Jing", "WANG J", "单名 - 不应拆分"),
        ("Li Wei", "LI W", "单名 - 不应拆分"),

        # --- 组3: 外国名 (不应误拆) ---
        ("Lee Simona", "LEE S", "外国名 Simona - 不应拆为 S M"),
        ("Han Solo", "HAN S", "外国名 Solo - 不应拆为 S L"),
        ("James Lebron", "JAMES L", "外国名 Lebron - bron非拼音，不拆"),
        ("Tan Christopher", "TAN C", "外国名 Christopher - 不拆"),
        ("Albert Einstein", "EINSTEIN A", "标准外国名"),
        ("Ludwig van Beethoven", "VAN BEETHOVEN L", "带前缀的复姓"),

        # --- 组4: 已有格式 (保持原样) ---
        ("Han, Shao-Heng", "HAN S H", "已有连字符"),
        ("Han, Shao Heng", "HAN S H", "已有空格"),

        # --- 组5: 复杂拼音边界 ---
        ("Lin Yingying", "LIN Y Y", "Ying ying"),
        ("Xu Xian", "XU X", "Xian 是单字 - 不应拆为 Xi an"),
        ("Fan Bingbing", "FAN B B", "Bing bing"),
        ("Ma Yo-Yo", "MA Y Y", "Yo-Yo 连字符")
    ]

    success_count = 0
    fail_count = 0

    print(f"{'输入':<25} | {'预期':<15} | {'实际':<15} | {'结果'}")
    print("-" * 75)

    for raw_name, expected, note in test_cases:
        actual = format_western_name(raw_name)
        is_pass = (actual == expected)
        status = "✅ PASS" if is_pass else "❌ FAIL"
        if is_pass:
            success_count += 1
        else:
            fail_count += 1

        print(f"{raw_name:<25} | {expected:<15} | {actual:<15} | {status}")
        if not is_pass:
            print(f"   >>> 失败原因: {note}")

    print("-" * 75)
    print(f"测试结束: 成功 {success_count} / 总计 {len(test_cases)}")
```

---

### 📄 `services\orchestrator.py`

```python:services\orchestrator.py
"""
文件路径: services/orchestrator.py
=========================================================
【接口说明】
def format_batch(self, raw_text_block: str, callback_signal=None) -> dict:
    '''
    批量处理
    返回字典包含:
    - "with_num": 纯文本（带序号） -> 用于复制
    - "no_num":   纯文本（无序号） -> 用于复制
    - "display_html": HTML格式（带链接） -> 用于界面显示
    '''
=========================================================
"""

import sys
import os
import time
import re
import difflib
import html  # 【新增】用于转义 HTML 特殊字符
import config
from services import formatter
from services.api_engines.openalex_engine import OpenAlexEngine
from services.api_engines.crossref import CrossrefEngine
from services.api_engines.semantic_scholar import SemanticScholarEngine


class Orchestrator:
    """总指挥"""

    def __init__(self):
        self.engines = []
        self._init_engines()

    def _init_engines(self):
        print("--- [调试] 正在初始化引擎 ---")
        if config.SourceConfig.OPENALEX_ENABLED: self.engines.append(OpenAlexEngine())
        if config.SourceConfig.CROSSREF_ENABLED: self.engines.append(CrossrefEngine())
        if config.SourceConfig.S2_ENABLED: self.engines.append(SemanticScholarEngine())
        print(f"--- [调试] 引擎初始化完毕，共加载 {len(self.engines)} 个引擎")

    def format_batch(self, raw_text_block: str, callback_signal=None) -> dict:
        """批量处理"""
        lines = raw_text_block.split('\n')
        list_with_num = []
        list_no_num = []
        list_html = []  # 【新增】用于存储 HTML 显示内容

        total = len(lines)

        for i, line in enumerate(lines):
            original_line = line.strip()
            if not original_line:
                continue

            print(f"--- [调试] 处理第 {i + 1} 条 ---")

            # 分离序号
            match = re.match(r'^\s*(\[\d+\]|\d+\.|\d+、|\(\d+\))\s*(.*)', original_line)
            prefix = ""
            clean_query = original_line
            if match:
                prefix = match.group(1)
                clean_query = match.group(2)

            # 处理单条 (现在返回 3 个值: 文本, 是否成功, URL)
            formatted_content, is_success, url = self._format_single_with_status(clean_query)

            # 通过 callback 发送状态: "PREV_OK" 或 "PREV_FAIL"
            if callback_signal:
                progress = int(((i + 1) / total) * 100)
                status_tag = "PREV_OK" if is_success else "PREV_FAIL"
                next_msg = f"正在处理: {clean_query[:15]}..."
                callback_signal(progress, f"{status_tag}|{next_msg}")

            # 1. 构建纯文本结果 (用于复制)
            list_no_num.append(formatted_content)
            full_text_line = f"{prefix} {formatted_content}" if prefix else formatted_content
            list_with_num.append(full_text_line)

            # 2. 构建 HTML 结果 (用于显示和点击)
            # 使用 html.escape 防止标题中的 < > 等字符破坏 HTML 结构
            safe_text = html.escape(full_text_line)

            if is_success and url:
                # 成功且有链接：包裹 <a> 标签，并加一个小的链接图标提示
                # 样式说明：text-decoration:none 去掉下划线，颜色交给 CSS 控制
                html_line = (
                    f'<div style="margin-bottom: 12px;">'
                    f'<a href="{url}" title="点击跳转原文: {url}">'
                    f'{safe_text} <span style="font-size:12px; vertical-align:middle;">🔗</span>'
                    f'</a>'
                    f'</div>'
                )
            elif is_success:
                # 成功但无链接
                html_line = f'<div style="margin-bottom: 12px; color:#2c3e50;">{safe_text}</div>'
            else:
                # 失败：用灰色或红色显示，不加链接
                html_line = f'<div style="margin-bottom: 12px; color:#7f8c8d;">{safe_text}</div>'

            list_html.append(html_line)

            if i < total - 1:
                time.sleep(config.MIN_REQUEST_INTERVAL)

        return {
            "with_num": "\n\n".join(list_with_num),
            "no_num": "\n\n".join(list_no_num),
            "display_html": "".join(list_html)  # HTML 不需要换行符，div 自带换行
        }

    def _format_single_with_status(self, query: str) -> (str, bool, str):
        """
        内部辅助方法
        返回: (格式化后的文本, 是否成功, 原文URL)
        """
        if not self.engines:
            return f"{query} ❌ (未启用API)", False, ""
        if len(query) < 4:
            return f"{query} ❌", False, ""

        is_pure_doi = "10." in query and "/" in query and len(query.split()) < 2
        if is_pure_doi: query = query.strip()

        for engine in self.engines:
            try:
                citation_data = engine.search(query)
                if citation_data:
                    is_match, reason = self._validate_result(query, citation_data)
                    if is_match:
                        # 成功！返回 URL
                        return formatter.to_gbt7714(citation_data), True, citation_data.url
                    else:
                        continue
            except Exception:
                continue

        # 失败
        return f"{query} ❌", False, ""

    def format_single(self, query: str) -> str:
        """兼容旧接口"""
        res, _, _ = self._format_single_with_status(query)
        return res

    def _validate_result(self, user_query: str, data) -> (bool, str):
        if not data.title: return False, "无标题"
        query_lower = user_query.lower()
        title_lower = data.title.lower()
        if data.doi and data.doi.lower() in query_lower: return True, "DOI匹配"
        similarity = difflib.SequenceMatcher(None, query_lower, title_lower).ratio()
        if similarity > 0.7: return True, "相似度达标"
        query_words = [w for w in re.split(r'\W+', query_lower) if len(w) > 3]
        if not query_words: return True, "输入过短"
        hit_count = sum(1 for w in query_words if w in title_lower)
        if hit_count / len(query_words) > 0.7: return True, "关键词覆盖"
        has_author = False
        if data.authors:
            for auth in data.authors:
                for p in auth.lower().split():
                    if len(p) > 2 and p in query_lower:
                        has_author = True
                        break
        has_year = data.year and (str(data.year) in query_lower)
        if has_author and has_year: return True, "作者年份匹配"
        if query_lower in title_lower or title_lower in query_lower: return True, "包含关系"
        return False, f"相似度低({similarity:.2f})"
```

---

### 📄 `services\__init__.py`

```python:services\__init__.py

```

---

### 📄 `services\api_engines\base_engine.py`

```python:services\api_engines\base_engine.py
"""
文件路径: services/api_engines/base_engine.py
=========================================================
【可用接口说明】

class BaseEngine:
    # --- 必须被子类重写的方法 ---
    def search(self, query: str) -> CitationData:
        '''
        输入: 用户给的原始文本 (query)
        输出: 标准化的 CitationData 对象
        '''
        pass

    # --- 通用工具方法 ---
    def get_headers(self) -> dict:
        '''自动生成带身份标识的 HTTP 请求头'''
        pass
=========================================================
"""

from abc import ABC, abstractmethod
import requests
from typing import Optional
import logging

# 引入我们的标准数据模型和配置
from models.citation_model import CitationData
import config

class BaseEngine(ABC):
    """
    所有 API 引擎的父类。
    作用：强制规定所有子类（OpenAlex, Crossref等）必须长什么样，
    避免未来代码乱七八糟。
    """

    def __init__(self):
        self.name = "BaseEngine"
        # 配置日志，方便调试
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

    def get_headers(self) -> dict:
        """
        生成标准请求头。
        根据 config.py 中的配置，带上 User-Agent，
        这是防封号的关键一步。
        """
        return {
            "User-Agent": config.USER_AGENT,
            "Accept": "application/json" # 告诉服务器我们要 JSON 数据
        }

    @abstractmethod
    def search(self, query: str) -> Optional[CitationData]:
        """
        核心抽象方法。
        子类必须实现这个方法，否则报错。
        """
        pass

    def safe_request(self, url: str, params: dict = None) -> Optional[dict]:
        """
        通用的网络请求发送器。
        封装了超时处理、错误捕获，防止因为断网导致程序闪退。
        """
        try:
            response = requests.get(
                url,
                headers=self.get_headers(),
                params=params,
                timeout=config.TIMEOUT
            )
            response.raise_for_status() # 如果状态码不是200，抛出异常
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"[{self.name}] 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"[{self.name}] 未知错误: {e}")
            return None
```

---

### 📄 `services\api_engines\cnki.py`

```python:services\api_engines\cnki.py
"""
文件路径: services/api_engines/cnki.py
=========================================================
【可用接口说明】

class CnkiEngine(BaseEngine):
    def search(self, query: str) -> CitationData:
        '''
        策略: 百度(首选) -> Bing(备选) -> 搜狗(保底)
        解决: 百度403 & Bing验证码问题
        '''
        pass
=========================================================
"""

# ==============================================================================
# 👇 1. 必填：请填入您的百度 Cookie (这是最稳的方案，如果下面代码跑不通，请务必填这个)
MANUAL_COOKIE = ""
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import re
import uuid
import os

from services.api_engines.base_engine import BaseEngine
from models.citation_model import CitationData
import config


class CnkiEngine(BaseEngine):
    """
    知网 (CNKI) 搜索引擎 - 三通道生存狂版 (Baidu + Bing + Sogou)
    """

    def __init__(self):
        super().__init__()
        self.name = "CNKI_Proxy"
        self.session = requests.Session()

    def get_headers(self, source="baidu") -> dict:
        """根据不同的源生成伪装请求头"""
        # 随机选用一个浏览器头，增加通过率
        ua_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        ua = random.choice(ua_list)

        headers = {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        }

        if source == "baidu":
            headers['Referer'] = 'https://xueshu.baidu.com/'
            if MANUAL_COOKIE: headers['Cookie'] = MANUAL_COOKIE
        elif source == "bing":
            headers['Referer'] = 'https://www.bing.com/'
        elif source == "sogou":
            headers['Referer'] = 'https://scholar.sogou.com/'
            # 搜狗有时候需要一个假的 Cookie 才能跑
            headers['Cookie'] = f'SUV={int(time.time() * 1000)};'

        return headers

    def search(self, query: str) -> CitationData:
        """总入口：三级火箭策略"""

        # 1. 尝试百度 (最全)
        res = self.search_via_baidu(query)
        if res: return res

        # 2. 尝试 Bing (最快)
        self.logger.warning(f"[{self.name}] 百度通道失效，切换至 Bing...")
        res = self.search_via_bing(query)
        if res: return res

        # 3. 尝试 搜狗 (最后的希望)
        self.logger.warning(f"[{self.name}] Bing 通道失效 (验证码)，切换至 搜狗(Sogou)...")
        return self.search_via_sogou(query)

    def search_via_baidu(self, query: str):
        url = "https://xueshu.baidu.com/s"
        params = {'wd': f"{query} site:cnki.net", 'tn': 'SE_baiduxueshu_c1gjeupa', 'ie': 'utf-8'}
        self.logger.info(f"[{self.name}] 通道 [1/3]: 百度学术...")
        try:
            resp = self.session.get(url, params=params, headers=self.get_headers("baidu"), timeout=5)
            if resp.status_code == 200 and "验证码" not in resp.text:
                soup = BeautifulSoup(resp.text, 'html.parser')
                item = soup.find('div', class_='sc_content')
                if item: return self._parse_baidu_html(item)
            else:
                self.logger.warning(f"[{self.name}] 百度 403/验证码。")
        except Exception:
            pass
        return None

    def search_via_bing(self, query: str):
        url = "https://www.bing.com/search"
        params = {'q': f"{query} site:cnki.net"}
        self.logger.info(f"[{self.name}] 通道 [2/3]: Bing...")
        try:
            resp = self.session.get(url, params=params, headers=self.get_headers("bing"), timeout=5)
            # Bing 的验证码页面也是 200 OK，所以要查内容
            if "captcha" in resp.text or "challenge" in resp.url:
                self.logger.warning(f"[{self.name}] Bing 触发验证码。")
                return None

            soup = BeautifulSoup(resp.text, 'html.parser')
            # 寻找结果列表
            items = soup.find_all('li', class_='b_algo')
            for item in items:
                data = self._parse_bing_html(item)
                if data and data.title: return data
        except Exception:
            pass
        return None

    def search_via_sogou(self, query: str):
        url = "https://scholar.sogou.com/xueshu"
        params = {'ie': 'utf-8', 'query': query}
        self.logger.info(f"[{self.name}] 通道 [3/3]: 搜狗学术...")

        try:
            resp = self.session.get(url, params=params, headers=self.get_headers("sogou"), timeout=8)
            resp.encoding = 'utf-8'

            if "验证码" in resp.text or "antispider" in resp.url:
                self.logger.warning(f"[{self.name}] 搜狗也触发了验证码...")
                # 最后的挣扎：保存搜狗页面看看
                with open("debug_sogou_error.html", "w", encoding="utf-8") as f: f.write(resp.text)
                return None

            soup = BeautifulSoup(resp.text, 'html.parser')
            # 搜狗结果通常在 div.results > div.vrwrap
            results = soup.find_all('div', class_='vrwrap')

            if not results:
                self.logger.info(f"[{self.name}] 搜狗未找到结果。")
                return None

            # 找第一个结果
            for item in results:
                # 搜狗解析逻辑
                data = CitationData(entry_type="article", raw_data={"source": "Sogou"})

                # 1. 标题 (h3.tit > a)
                h3 = item.find('h3', class_='tit')
                if h3 and h3.find('a'):
                    data.title = h3.find('a').get_text(strip=True)
                    data.url = "https://scholar.sogou.com" + h3.find('a').get('href', '')

                # 2. 信息 (div.info)
                # 格式: 作者 - 期刊 - 年份
                info_div = item.find('div', class_='info')
                if info_div:
                    # 提取年份
                    text = info_div.get_text(" ", strip=True)
                    year_match = re.search(r'\b(19|20)\d{2}\b', text)
                    if year_match: data.year = year_match.group(0)

                    # 尝试提取作者 (span.p1 或者是第一个 - 之前的内容)
                    # 搜狗比较乱，我们简单分割
                    parts = text.split('-')
                    if len(parts) >= 1:
                        # 假设第一部分是作者
                        data.authors = parts[0].strip().split(',')
                    if len(parts) >= 2:
                        # 假设第二部分是期刊
                        possible_journal = parts[1].strip()
                        if not possible_journal.isdigit():
                            data.source = possible_journal

                if data.title:
                    return data

        except Exception as e:
            self.logger.error(f"[{self.name}] 搜狗通道出错: {e}")

        return None

    def _parse_baidu_html(self, item_soup) -> CitationData:
        """复用之前的百度解析"""
        citation = CitationData(entry_type="article", raw_data={"source": "Baidu"})
        try:
            t = item_soup.find('h3', class_='t')
            if t and t.find('a'): citation.title = t.find('a').get_text(strip=True)

            info = item_soup.find('div', class_='sc_info')
            if info:
                txt = info.get_text(" ", strip=True)
                ym = re.search(r'\b(19|20)\d{2}\b', txt)
                if ym: citation.year = ym.group(0)

                js = info.find('span', class_='sc_journal')
                if js: citation.source = js.get_text(strip=True)
        except:
            pass
        return citation

    def _parse_bing_html(self, item_soup) -> CitationData:
        """复用之前的 Bing 解析"""
        citation = CitationData(entry_type="article", raw_data={"source": "Bing"})
        try:
            h2 = item_soup.find('h2')
            if h2 and h2.find('a'):
                citation.title = h2.find('a').get_text(strip=True)
                citation.url = h2.find('a').get('href', '')

            cap = item_soup.find('div', class_='b_caption')
            if cap:
                txt = cap.get_text(" ", strip=True)
                ym = re.search(r'\b(19|20)\d{2}\b', txt)
                if ym: citation.year = ym.group(0)
        except:
            pass
        return citation
```

---

### 📄 `services\api_engines\crossref.py`

```python:services\api_engines\crossref.py
"""
文件路径: services/api_engines/crossref.py
=========================================================
【可用接口说明】

class CrossrefEngine(BaseEngine):
    def search(self, query: str) -> CitationData:
        '''
        输入: 论文标题 (支持中文) 或 DOI
        输出: 及其标准的 CitationData 对象
        优势: 官方API，极其稳定，无验证码，不封IP
        '''
        pass
=========================================================
"""

import urllib.parse
from typing import Optional
from services.api_engines.base_engine import BaseEngine
from models.citation_model import CitationData
import config


class CrossrefEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "Crossref"
        self.api_url = config.SourceConfig.CROSSREF_API_URL
        # Crossref 建议在 Header 中带上邮箱，进入 "Polite Pool"，速度更快且更稳定
        self.email = config.CONTACT_EMAIL

    def get_headers(self) -> dict:
        headers = super().get_headers()
        if self.email and "example.com" not in self.email:
            headers["User-Agent"] += f" (mailto:{self.email})"
        return headers

    def search(self, query: str) -> Optional[CitationData]:
        if not config.SourceConfig.CROSSREF_ENABLED:
            return None

        # 1. 智能判断：如果是 DOI 格式，直接精确查询
        # 简单判断是否包含 "10." 开头的 DOI 特征
        is_doi = "10." in query and "/" in query

        params = {}
        if is_doi:
            # 如果看起来像 DOI，清理一下直接查
            clean_doi = query.strip()
            # 移除可能的前缀
            if "doi.org/" in clean_doi:
                clean_doi = clean_doi.split("doi.org/")[-1]

            # Crossref 单个作品查询不需要参数，直接拼在 URL 后面
            # 但为了统一架构，我们还是用 query.bibliographic 搜索模式，容错率高
            params = {
                "query.bibliographic": clean_doi,
                "rows": 1
            }
        else:
            # 普通标题搜索
            params = {
                "query.bibliographic": query,
                "rows": 1,
                # 启用相关性排序
                "sort": "relevance"
            }

        self.logger.info(f"[{self.name}] 正在请求 API: {query[:20]}...")

        # 2. 发送请求
        data = self.safe_request(self.api_url, params)

        # 3. 解析数据
        if not data or "message" not in data or "items" not in data["message"]:
            return None

        items = data["message"]["items"]
        if not items:
            self.logger.info(f"[{self.name}] 未找到结果。")
            return None

        # 取第一条最佳匹配
        best_match = items[0]

        # 4. 转换为模型
        return self._parse_json_to_model(best_match)

    def _parse_json_to_model(self, item: dict) -> CitationData:
        citation = CitationData()
        citation.raw_data = item
        citation.entry_type = "article"  # 默认为文章

        # A. 标题 (Crossref 返回的是列表)
        if "title" in item and item["title"]:
            citation.title = item["title"][0]

        # B. 作者
        if "author" in item:
            authors = []
            for a in item["author"]:
                # 拼接 姓 + 名
                given = a.get("given", "")
                family = a.get("family", "")
                full_name = f"{given} {family}".strip()
                if full_name:
                    authors.append(full_name)
            citation.authors = authors

        # C. 来源 (期刊名)
        if "container-title" in item and item["container-title"]:
            citation.source = item["container-title"][0]

        # D. 年份 (结构较深: published-print -> date-parts -> [[2023, 1, 1]])
        date_parts = None
        if "published-print" in item:
            date_parts = item["published-print"]["date-parts"]
        elif "published-online" in item:
            date_parts = item["published-online"]["date-parts"]
        elif "created" in item:  # 保底
            date_parts = item["created"]["date-parts"]

        if date_parts and date_parts[0]:
            citation.year = str(date_parts[0][0])

        # E. 卷期页
        citation.volume = item.get("volume", "")
        citation.issue = item.get("issue", "")
        citation.pages = item.get("page", "")
        citation.doi = item.get("DOI", "")
        citation.url = item.get("URL", "")

        return citation
```

---

### 📄 `services\api_engines\dblp.py`

```python:services\api_engines\dblp.py

```

---

### 📄 `services\api_engines\openalex_engine.py`

```python:services\api_engines\openalex_engine.py
"""
文件路径: services/api_engines/openalex_engine.py
=========================================================
【可用接口说明】

class OpenAlexEngine(BaseEngine):
    def search(self, query: str) -> CitationData:
        # 输入标题，返回数据
        pass
=========================================================
"""

import sys
import os

# === 路径修复代码 (必须放在最前面) ===
# 1. 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)
# 2. 获取当前文件所在目录 (services/api_engines)
current_dir = os.path.dirname(current_file_path)
# 3. 获取项目根目录 (向上跳两级: services -> project_root)
project_root = os.path.dirname(os.path.dirname(current_dir))
# 4. 将根目录加入 Python 搜索路径，解决 "ModuleNotFoundError"
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ==========================================

from typing import Optional
from services.api_engines.base_engine import BaseEngine
from models.citation_model import CitationData
import config


class OpenAlexEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "OpenAlex"
        self.api_url = config.SourceConfig.OPENALEX_API_URL

    def search(self, query: str) -> Optional[CitationData]:
        """
        实现 OpenAlex 的具体搜索逻辑
        """
        if not config.SourceConfig.OPENALEX_ENABLED:
            return None

        # 1. 准备参数
        # OpenAlex 的搜索参数通常是filter或者search
        # 这里使用 search 模式匹配标题
        params = {
            "search": query,
            "per_page": 1  # 我们只需要匹配度最高的那一条
        }

        # 2. 发送请求 (使用父类的安全方法)
        data = self.safe_request(self.api_url, params)

        # 3. 解析数据
        if not data or "results" not in data or not data["results"]:
            self.logger.info(f"[{self.name}] 未找到结果: {query[:20]}...")
            return None

        # 拿到第一条最佳匹配结果
        best_match = data["results"][0]

        # 4. 【核心】数据映射 (Data Mapping)
        # 将 OpenAlex 的 JSON 格式 转换为 我们的 CitationData 格式
        return self._parse_json_to_model(best_match)

    def _parse_json_to_model(self, json_data: dict) -> CitationData:
        """
        私有方法：处理复杂的 JSON 结构
        """
        # 创建空模型
        citation = CitationData()

        # A. 提取标题
        citation.title = json_data.get("display_name", "")

        # B. 提取作者 (OpenAlex 的作者在 authorships 列表里)
        # 结构: authorships -> [ {author: {display_name: "Name"}} ]
        authors_raw = json_data.get("authorships", [])
        citation.authors = [
            item.get("author", {}).get("display_name", "")
            for item in authors_raw
        ]

        # C. 提取来源 (期刊/会议)
        # 结构: primary_location -> source -> display_name
        primary_loc = json_data.get("primary_location") or {}
        source_info = primary_loc.get("source") or {}
        citation.source = source_info.get("display_name", "")

        # D. 提取年份
        citation.year = str(json_data.get("publication_year", ""))

        # E. 提取卷期页 (OpenAlex 放在 biblio 字典里)
        biblio = json_data.get("biblio", {})
        citation.volume = biblio.get("volume", "")
        citation.issue = biblio.get("issue", "")
        citation.pages = f"{biblio.get('first_page', '')}-{biblio.get('last_page', '')}"

        # 清理页码格式 (如果只有first_page没last_page，去掉横杠)
        if citation.pages == "-":
            citation.pages = ""
        elif citation.pages.endswith("-"):
            citation.pages = citation.pages.strip("-")

        # F. 提取 DOI
        # OpenAlex 返回的 DOI 通常是完整 URL (https://doi.org/10.xxx/xxx)
        # 我们只需要后面的 10.xxx 部分
        doi_url = json_data.get("doi", "")
        if doi_url:
            citation.doi = doi_url.replace("https://doi.org/", "").replace("http://doi.org/", "")

        # G. 保存原始数据备查
        citation.raw_data = json_data

        return citation


# --- 单元测试代码 (仅在直接运行此文件时执行) ---
if __name__ == "__main__":
    # 这一块代码是教你如何单独测试这个文件的
    print("正在测试 OpenAlex 引擎...")
    engine = OpenAlexEngine()
    test_query = "Deep learning Nature 2015"
    result = engine.search(test_query)

    if result:
        print("✅ 测试成功!")
        print(f"标题: {result.title}")
        print(f"作者: {result.authors}")
        print(f"年份: {result.year}")
        print(f"期刊: {result.source}")
        print(f"页码: {result.pages}")
    else:
        print("❌ 测试失败或无结果")
```

---

### 📄 `services\api_engines\semantic_scholar.py`

```python:services\api_engines\semantic_scholar.py
"""
文件路径: services/api_engines/semantic_scholar.py
=========================================================
【可用接口说明】

class SemanticScholarEngine(BaseEngine):
    def search(self, query: str) -> CitationData:
        '''
        输入: 论文标题
        输出: CitationData 对象
        优势: AI 驱动，搜索精度高，覆盖全球文献
        '''
        pass
=========================================================
"""

from typing import Optional
from services.api_engines.base_engine import BaseEngine
from models.citation_model import CitationData
import config

class SemanticScholarEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.name = "SemanticScholar"
        # 官方图谱 API 搜索端点
        self.api_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.api_key = config.SourceConfig.S2_API_KEY

    def get_headers(self) -> dict:
        headers = super().get_headers()
        # 如果用户申请了 Key (免费的)，带上可以提高限额
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def search(self, query: str) -> Optional[CitationData]:
        if not config.SourceConfig.S2_ENABLED:
            return None

        # 1. 构造参数
        # fields 参数指定我们需要返回哪些字段，避免数据冗余
        params = {
            "query": query,
            "limit": 1,
            "fields": "title,authors,year,venue,url,externalIds,publicationTypes"
        }

        self.logger.info(f"[{self.name}] 正在请求 API: {query[:20]}...")

        # 2. 发送请求
        data = self.safe_request(self.api_url, params)

        # 3. 解析
        if not data or "data" not in data or not data["data"]:
            self.logger.info(f"[{self.name}] 未找到结果。")
            return None

        best_match = data["data"][0]
        return self._parse_json_to_model(best_match)

    def _parse_json_to_model(self, item: dict) -> CitationData:
        citation = CitationData()
        citation.raw_data = item
        citation.entry_type = "article"

        # A. 标题
        citation.title = item.get("title", "")

        # B. 作者 (列表字典)
        if "authors" in item and item["authors"]:
            citation.authors = [a["name"] for a in item["authors"] if "name" in a]

        # C. 年份
        citation.year = str(item.get("year", ""))

        # D. 来源 (venue)
        citation.source = item.get("venue", "")

        # E. 链接 & DOI
        citation.url = item.get("url", "")
        if "externalIds" in item and item["externalIds"]:
            citation.doi = item["externalIds"].get("DOI", "")

        return citation
```

---

### 📄 `services\api_engines\__init__.py`

```python:services\api_engines\__init__.py

```

---

### 📄 `ui_framework\base_chart.py`

```python:ui_framework\base_chart.py
import csv
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMenu)
from PySide6.QtCore import Qt, Signal

# Matplotlib 相关
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import rcParams

# 导入样式
from chart_styles import BTN_STYLE_NORMAL, BTN_STYLE_PRIMARY, TABLE_STYLE, MENU_STYLE

# 全局字体设置
rcParams['font.family'] = 'Microsoft YaHei'
rcParams['axes.unicode_minus'] = False
rcParams['font.size'] = 9


class BaseChartWidget(QWidget):
    """
    通用图表控件基类
    包含：Matplotlib 画布 + 底部/右侧数据表格 + 常用工具栏
    """
    # 信号：当数据被修改或文件被拖入时发射
    data_modified = Signal(list)
    file_dropped = Signal(str)

    def __init__(self, parent=None, show_table=True):
        super().__init__(parent)
        self.current_data = []  # 存储当前数据

        # 1. 布局初始化
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 2. 初始化 Matplotlib 画布
        self.fig = Figure(figsize=(5, 4), dpi=100, facecolor='white')
        # 调整边距，防止标签被遮挡
        self.fig.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.15)

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.ax = self.fig.add_subplot(111)

        # 【关键】修复滚动问题：强制忽略滚轮事件，防止与页面滚动冲突
        self.canvas.wheelEvent = lambda event: event.ignore()

        layout.addWidget(self.canvas, stretch=10)

        # 3. 工具栏区域
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 10, 0)

        # 预留左侧按钮槽（子类可以往这里加按钮）
        self.left_btn_layout = QHBoxLayout()
        btn_layout.addLayout(self.left_btn_layout)

        btn_layout.addStretch()

        # 右侧默认功能按钮
        self.btn_export_csv = QPushButton("📊 导出数据")
        self.btn_export_csv.setStyleSheet(BTN_STYLE_NORMAL)
        self.btn_export_csv.clicked.connect(self.export_csv)

        self.btn_export_img = QPushButton("🖼️ 导出图像")
        self.btn_export_img.setStyleSheet(BTN_STYLE_NORMAL)
        self.btn_export_img.clicked.connect(self.export_image)

        btn_layout.addWidget(self.btn_export_csv)
        btn_layout.addWidget(self.btn_export_img)
        layout.addLayout(btn_layout)

        # 4. 数据表格 (可选)
        if show_table:
            self.table = QTableWidget()
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["X 值", "Y 值"])  # 默认表头
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.verticalHeader().setVisible(False)
            self.table.setAlternatingRowColors(True)
            self.table.setStyleSheet(TABLE_STYLE)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            self.table.setMaximumHeight(150)

            # 右键菜单策略
            self.table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.table.customContextMenuRequested.connect(self.show_context_menu)

            layout.addWidget(self.table, stretch=3)

        # 初始化图表风格
        self._apply_chart_style()

    def _apply_chart_style(self):
        """应用美观的图表样式 (灰色边框、虚线网格)"""
        self.ax.clear()
        self.ax.set_facecolor('white')
        # 隐藏上、右边框
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        # 设置左、下边框颜色
        self.ax.spines['left'].set_color('#dcdfe6')
        self.ax.spines['bottom'].set_color('#dcdfe6')
        # 网格线设置
        self.ax.grid(True, linestyle=':', alpha=0.6, color='#909399')
        # 刻度线设置
        self.ax.tick_params(axis='both', which='both', direction='in',
                            length=4, width=1, color='#606266', labelcolor='#606266')

    def update_chart(self, x_data, y_data, title="图表标题", xlabel="X轴", ylabel="Y轴"):
        """
        子类直接调用此方法来刷新图表
        """
        self._apply_chart_style()  # 重置样式

        self.ax.set_title(title, fontsize=10, fontweight='bold', color='#303133', pad=10)
        self.ax.set_xlabel(xlabel, fontsize=9, color='#606266')
        self.ax.set_ylabel(ylabel, fontsize=9, color='#606266')

        # 绘制曲线
        self.ax.plot(x_data, y_data, color="#e74c3c", linewidth=2, label="Data")

        # 刷新画布
        self.canvas.draw()

        # 刷新表格 (如果有)
        if hasattr(self, 'table'):
            self._update_table(x_data, y_data)

    def _update_table(self, x_data, y_data):
        """内部方法：更新表格数据"""
        rows = min(len(x_data), 1000)  # 限制显示数量防止卡顿
        self.table.setRowCount(rows)
        self.table.setSortingEnabled(False)
        for i in range(rows):
            self.table.setItem(i, 0, QTableWidgetItem(f"{x_data[i]:.4f}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{y_data[i]:.4f}"))
        self.table.setSortingEnabled(True)

    def export_image(self):
        """通用导出图片功能"""
        file_path, _ = QFileDialog.getSaveFileName(self, "导出图片", "chart.png",
                                                   "PNG Image (*.png);;JPEG Image (*.jpg)")
        if file_path:
            try:
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", f"图片已保存:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def export_csv(self):
        """通用导出数据功能"""
        if not hasattr(self, 'table') or self.table.rowCount() == 0:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "导出数据", "data.csv", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    # 获取表头
                    headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                    writer.writerow(headers)
                    # 获取内容
                    for row in range(self.table.rowCount()):
                        row_data = []
                        for col in range(self.table.columnCount()):
                            item = self.table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                QMessageBox.information(self, "成功", f"数据已导出至:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def show_context_menu(self, pos):
        """表格右键菜单 (可重写)"""
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        menu.addAction("刷新图表", lambda: None)
        menu.exec(self.table.mapToGlobal(pos))
```

---

### 📄 `ui_framework\base_dialogs.py`

```python:ui_framework\base_dialogs.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QGroupBox,
                               QScrollArea, QWidget, QFrame, QDialogButtonBox,
                               QLineEdit, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt
# 导入刚才写的样式工具
from ui_styles import apply_dialog_theme


class BaseScrollFormDialog(QDialog):
    """
    【通用高级模板】
    自带滚动条、美化的 GroupBox 和底部按钮栏。
    使用方法：继承此类，然后在 self.form_layout 中添加内容。
    """

    def __init__(self, title="新窗口", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(550, 700)  # 默认大小，可改

        # 1. 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 2. 滚动区域 (核心样式在这里)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.content_widget = QWidget()
        # 这里提取了你原项目中最漂亮的样式代码
        self.content_widget.setStyleSheet("""
            QWidget { background-color: #ffffff; }
            QGroupBox { 
                font-weight: bold; color: #333; 
                border: 1px solid #dcdfe6; border-radius: 6px; 
                margin-top: 10px; padding-top: 15px; font-size: 13px; 
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
                border: 1px solid #ccc; border-radius: 4px; padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus { border: 1px solid #3498db; }
        """)

        # 供子类使用的布局
        self.form_layout = QVBoxLayout(self.content_widget)
        self.form_layout.setContentsMargins(25, 25, 25, 25)
        self.form_layout.setSpacing(20)

        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)

        # 3. 底部按钮区
        btn_container = QWidget()
        btn_container.setStyleSheet("background-color: #f5f5f5; border-top: 1px solid #ddd;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(20, 15, 20, 15)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText("确定")
        self.buttons.button(QDialogButtonBox.Cancel).setText("取消")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        # 应用统一样式
        apply_dialog_theme(self, self.buttons)

        btn_layout.addStretch()
        btn_layout.addWidget(self.buttons)
        self.main_layout.addWidget(btn_container)

    def add_group(self, title):
        """快捷方法：添加一个分组框，并返回其内部的 FormLayout"""
        group = QGroupBox(title)
        layout = QFormLayout(group)
        layout.setVerticalSpacing(12)
        self.form_layout.addWidget(group)
        return layout


class SimpleInputDialog(QDialog):
    """
    【通用简单模板】
    只有两个输入框，类似于原来的新建项目。
    """

    def __init__(self, title="输入", label1="名称:", label2="描述:", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 200)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        form = QFormLayout()
        self.input1 = QLineEdit()
        self.input2 = QLineEdit()

        form.addRow(label1, self.input1)
        if label2:
            form.addRow(label2, self.input2)

        layout.addLayout(form)
        layout.addStretch()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText("确定")
        self.buttons.button(QDialogButtonBox.Cancel).setText("取消")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        apply_dialog_theme(self, self.buttons)
        layout.addWidget(self.buttons)

    def get_data(self):
        return self.input1.text(), self.input2.text()
```

---

### 📄 `ui_framework\base_splash.py`

```python:ui_framework\base_splash.py
from PySide6.QtWidgets import QSplashScreen, QProgressBar
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QRect

class BaseSplashScreen(QSplashScreen):
    def __init__(self, title="韩劭恒", subtitle="New Project v1.0", icon="🚀"):
        """
        通用启动页模板
        :param title: 主标题文字
        :param subtitle: 副标题或版本号文字
        :param icon: 中间的 Emoji 图标 (例如 '🔬', '🚀', '📊')
        """
        # 1. 动态绘制背景图 (600x350)
        width, height = 600, 350
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制圆角矩形背景 (保持了你的深蓝渐变风格)
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor("#2c3e50"))  # 深蓝
        gradient.setColorAt(1, QColor("#3498db"))  # 亮蓝

        rect = QRect(0, 0, width, height)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 15, 15)

        # 绘制 Logo/Emoji (使用传入的 icon 参数)
        font_icon = QFont("Segoe UI Emoji", 60)
        if not font_icon.exactMatch():
            font_icon = QFont("Apple Color Emoji", 60)
        painter.setFont(font_icon)
        painter.setPen(QColor("white"))
        painter.drawText(QRect(0, 50, width, 100), Qt.AlignCenter, icon)

        # 绘制主标题 (使用传入的 title 参数)
        font_title = QFont("Microsoft YaHei", 24, QFont.Bold)
        painter.setFont(font_title)
        painter.drawText(QRect(0, 160, width, 50), Qt.AlignCenter, title)

        # 绘制副标题/版本号 (使用传入的 subtitle 参数)
        font_sub = QFont("Microsoft YaHei", 12)
        painter.setFont(font_sub)
        painter.setPen(QColor("#ecf0f1"))
        painter.drawText(QRect(0, 210, width, 30), Qt.AlignCenter, subtitle)

        painter.end()

        super().__init__(pixmap)

        # 2. 添加进度条 (样式保持不变)
        self.progress = QProgressBar(self)
        self.progress.setGeometry(50, 280, 500, 8)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2ecc71; 
                border-radius: 4px;
            }
        """)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)

    def update_progress(self, value):
        self.progress.setValue(value)
```

---

### 📄 `ui_framework\base_window.py`

```python:ui_framework\base_window.py
# ui_framework/base_window.py
# ==============================================================================
# 修改说明:
# 1. 新增 resource_path 函数: 专门解决打包后找不到资源路径的问题
# 2. 修改 __init__ 中的 bg_path: 使用 resource_path 包裹文件名
# ==============================================================================

import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QLabel, QSizePolicy, QApplication)
from PySide6.QtGui import (QAction, QColor, QPixmap, QPainter,
                           QGuiApplication)
from PySide6.QtCore import Qt, QSize


def resource_path(relative_path):
    """
    【核心修复代码】资源路径导航仪
    获取资源的绝对路径。
    - 开发环境: 返回当前文件所在的相对路径
    - 打包环境(PyInstaller): 返回解压后的临时路径 (sys._MEIPASS)
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时路径
        return os.path.join(sys._MEIPASS, relative_path)

    # 普通开发环境
    return os.path.join(os.path.abspath("."), relative_path)


class BaseMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置默认标题
        self.setWindowTitle("参考文献国标刷")

        # === 1. 屏幕自适应设置 ===
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        new_width = int(screen_geometry.width() * 0.7)
        new_height = int(screen_geometry.height() * 0.75)
        self.resize(new_width, new_height)
        self.move(
            screen_geometry.x() + (screen_geometry.width() - new_width) // 2,
            screen_geometry.y() + (screen_geometry.height() - new_height) // 2
        )

        # === 2. 加载背景图片逻辑 ===
        self.bg_pixmap = None
        self.show_bg_image = True

        # 【修改点】: 使用 resource_path 获取真正的路径
        # 即使打包成 exe，也能在临时目录找到 background.jpg
        bg_path = resource_path("background.jpg")

        # 简单的存在性检查
        if os.path.exists(bg_path):
            self.bg_pixmap = QPixmap(bg_path)
            # print(f"✅ 已加载背景图: {bg_path}") # 调试用
        else:
            # 如果没找到，可以在控制台输出提示，方便排查
            print(f"⚠️ 未找到背景图: {bg_path} (请确保图片位于项目根目录)")

        # === 3. (已删除) 顶部工具栏 ===
        # 原有的 Home/Settings 按钮已移除，使界面更纯净

        # === 4. 左下角签名 ===
        self.signature_label = QLabel("@小白元宵", self)
        self.signature_label.setStyleSheet("""
            color: rgba(100, 100, 100, 150); 
            font-family: "Microsoft YaHei";
            font-size: 11px;
            font-weight: bold;
            background: transparent;
        """)
        self.signature_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.signature_label.adjustSize()

        # === 5. 中央主区域 ===
        self.central_widget = QWidget()
        self.central_widget.setAttribute(Qt.WA_TranslucentBackground)  # 必须透明
        self.setCentralWidget(self.central_widget)

        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)

    # === 事件处理 ===
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'signature_label'):
            self.signature_label.move(10, self.height() - self.signature_label.height() - 5)
            self.signature_label.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 绘制背景色 (淡蓝灰)
        painter.fillRect(self.rect(), QColor("#f0f2f5"))

        # 绘制背景图 (如果有)
        if self.show_bg_image and self.bg_pixmap and not self.bg_pixmap.isNull():
            # 【修改】将不透明度设置为 0.15，保持原来的淡淡的效果
            painter.setOpacity(0.15)

            # 保持比例铺满窗口
            scaled_pixmap = self.bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)

        painter.setOpacity(1.0)
```

---

### 📄 `ui_framework\chart_styles.py`

```python:ui_framework\chart_styles.py
# === 按钮样式 ===
BTN_STYLE_NORMAL = """
    QPushButton {
        background-color: white;
        border: 1px solid #dcdfe6;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        color: #606266;
    }
    QPushButton:hover {
        border-color: #409eff;
        color: #409eff;
        background-color: #ecf5ff;
    }
"""

BTN_STYLE_PRIMARY = """
    QPushButton {
        background-color: #e6f7ff;
        border: 1px solid #91d5ff;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        color: #1890ff;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1890ff;
        color: white;
    }
"""

BTN_STYLE_DANGER = """
    QPushButton {
        background-color: #fff0f0;
        border: 1px solid #ffccc7;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        color: #ff4d4f;
    }
    QPushButton:hover {
        background-color: #ff4d4f;
        color: white;
    }
"""

# === 表格样式 (带漂亮的表头和滚动条) ===
TABLE_STYLE = """
    QTableWidget {
        background-color: white;
        border: 1px solid #ebeef5;
        border-radius: 6px;
        gridline-color: #f2f6fc;
        font-size: 11px;
    }
    QHeaderView::section {
        background-color: #fafafe;
        color: #555;
        padding: 6px;
        border: none;
        border-bottom: 2px solid #e4e7ed;
        font-weight: bold;
        font-family: "Microsoft YaHei";
    }
    QTableWidget::item { padding: 4px; }
    QTableWidget::item:selected { background-color: #ecf5ff; color: #409eff; }

    /* 滚动条美化 */
    QScrollBar:vertical {
        border: none;
        background: #f4f6f9;
        width: 6px;
    }
    QScrollBar:handle:vertical {
        background: #c0c4cc;
        border-radius: 3px;
    }
"""

# === 右键菜单样式 ===
MENU_STYLE = """
    QMenu {
        background-color: #ffffff;
        border: 1px solid #f0f0f0;
        border-radius: 4px;
        padding: 4px 0px;
    }
    QMenu::item {
        background-color: transparent;
        color: #333333;
        padding: 6px 20px;
        margin: 2px 4px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #ecf5ff;
        color: #409eff;
    }
    QMenu::separator {
        height: 1px;
        background: #f0f0f0;
        margin: 4px 0px;
    }
"""
```

---

### 📄 `ui_framework\ui_styles.py`

```python:ui_framework\ui_styles.py
from PySide6.QtWidgets import (QDialogButtonBox, QDateTimeEdit, QDialog, QCalendarWidget)
from PySide6.QtCore import Qt, QDateTime, QTime

# === 1. 样式常量定义 ===

# 通用弹窗样式 (输入框、下拉菜单、滚动条修复)
DIALOG_STYLES = """
    QDialog { background-color: #ffffff; }
    QLabel { color: #2c3e50; font-size: 14px; font-weight: 600; font-family: "Microsoft YaHei"; }

    QLineEdit, QDoubleSpinBox, QDateTimeEdit, QTextEdit, QComboBox {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 6px 10px;
        background-color: #f9f9f9; 
        color: #333333;
        font-size: 14px;
        font-family: "Microsoft YaHei";
        min-height: 20px;
    }
    QLineEdit:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus, QTextEdit:focus, QComboBox:focus {
        background-color: #ffffff;
        border: 1px solid #3498db;
    }
    QLineEdit:read-only { background-color: #f0f0f0; color: #888; }

    /* 下拉菜单美化 */
    QComboBox::drop-down {
        border: none; background: transparent; width: 20px;
    }
    QComboBox QAbstractItemView {
        border: 1px solid #3498db;
        background-color: white;
        selection-background-color: #ecf5ff;
        selection-color: #3498db;
        outline: none;
        padding: 4px;
    }

    /* === 滚动条美化 (去除默认的丑陋背景) === */
    QScrollBar:vertical {
        border: none;
        background: #f9f9f9;
        width: 8px;
        margin: 0px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #dcdfe6;
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #c0c4cc;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

# 日历控件专属美化样式 (蓝色主题)
CALENDAR_STYLES = """
    /* 1. 整体背景和导航条 */
    QCalendarWidget QWidget#qt_calendar_navigationbar { 
        background-color: #3498db; 
        min-height: 35px;
    }
    QCalendarWidget QToolButton {
        color: white;
        background-color: transparent;
        border: none;
        font-weight: bold;
        icon-size: 20px;
        height: 30px;
    }
    QCalendarWidget QToolButton:hover {
        background-color: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }
    QCalendarWidget QToolButton::menu-indicator { image: none; }

    /* 2. 年份输入框和月份菜单 */
    QCalendarWidget QSpinBox {
        background-color: transparent;
        color: white;
        border: none;
        selection-background-color: rgba(255, 255, 255, 0.3);
        font-weight: bold;
    }
    QCalendarWidget QMenu { background-color: white; color: #333; border: 1px solid #ccc; }

    /* 3. 日期网格区域 */
    QCalendarWidget QAbstractItemView:enabled {
        background-color: white;
        color: #333;
        selection-background-color: #3498db; 
        selection-color: white;             
        font-family: "Microsoft YaHei";
        font-size: 13px;
        outline: none;
    }
    QCalendarWidget QAbstractItemView:disabled { color: #bbb; }
"""


# === 2. 工具函数 ===

def apply_dialog_theme(dialog: QDialog, button_box: QDialogButtonBox = None):
    """
    统一应用样式到对话框及其按钮
    """
    # 1. 应用 CSS
    dialog.setStyleSheet(DIALOG_STYLES)

    # 2. 如果传入了 button_box，专门美化确定/取消按钮
    if button_box:
        ok_btn = button_box.button(QDialogButtonBox.Ok)
        if ok_btn:
            ok_btn.setText("确定")
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #3498db; 
                    color: white; 
                    border: none; 
                    border-radius: 6px; 
                    padding: 8px 25px; 
                    font-weight: bold; 
                    font-size: 14px; 
                } 
                QPushButton:hover { background-color: #2980b9; }
            """)

        cancel_btn = button_box.button(QDialogButtonBox.Cancel)
        if cancel_btn:
            cancel_btn.setText("取消")
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #f1f2f6; 
                    color: #7f8c8d; 
                    border: none; 
                    border-radius: 6px; 
                    padding: 8px 25px; 
                    font-size: 14px; 
                } 
                QPushButton:hover { background-color: #e4e7eb; color: #2c3e50; }
            """)


def create_datetime_edit(init_dt=None, display_format="yyyy-MM-dd HH:mm"):
    """
    创建一个带有漂亮日历样式的日期时间选择器
    :param init_dt: 初始时间 (可以是字符串、QDateTime 或 None)
    :param display_format: 显示格式
    """
    dte = QDateTimeEdit()
    dte.setCalendarPopup(True)
    dte.setDisplayFormat(display_format)
    dte.setMinimumWidth(200)

    # 应用核心样式：对话框样式 + 日历样式
    dte.setStyleSheet(DIALOG_STYLES + CALENDAR_STYLES)

    # 时间初始化逻辑
    current = QDateTime.currentDateTime()
    # 默认设为整点，看起来整洁
    current.setTime(QTime(current.time().hour(), 0, 0))

    if init_dt:
        if isinstance(init_dt, str):
            # 尝试几种常见格式
            dt = QDateTime.fromString(init_dt, "yyyy-MM-dd HH:mm")
            if not dt.isValid():
                dt = QDateTime.fromString(init_dt, "yyyy-MM-dd-HH:00")  # 兼容你旧项目的格式

            if dt.isValid():
                dte.setDateTime(dt)
            else:
                dte.setDateTime(current)
        elif isinstance(init_dt, QDateTime):
            dte.setDateTime(init_dt)
    else:
        dte.setDateTime(current)

    return dte
```

---

### 📄 `ui_framework\__init__.py`

```python:ui_framework\__init__.py

```

---

### 📄 `views\main_view.py`

```python:views\main_view.py
# views/main_view.py
# ==============================================================================
# 模块名称: 主界面视图 (View) - 修复版
# 修复内容:
#   1. 将输出框改为 QTextBrowser 以支持 setOpenExternalLinks
#   2. 更新 CSS 样式以兼容 QTextBrowser
# ==============================================================================

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QTextBrowser,
                               QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect,
                               QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QFont

from ui_framework.base_window import BaseMainWindow


class MainView(BaseMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("参考文献国标刷 v.1.0")

        # 控件变量
        self.input_edit = None
        self.btn_convert = None
        self.output_edit = None
        self.status_label = None
        self.last_result_label = None

        self.btn_copy_with_num = None
        self.btn_copy_no_num = None

    def setup_ui(self):
        """构建 UI"""
        # --- 中央悬浮卡片 ---
        card_widget = QFrame()
        card_widget.setObjectName("MainCard")

        # 降低大卡片的不透明度
        card_widget.setStyleSheet("""
            #MainCard {
                background-color: rgba(255, 255, 255, 0.6);
                border-radius: 12px;
                border: 1px solid rgba(224, 224, 224, 0.6);
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 4)
        card_widget.setGraphicsEffect(shadow)

        card_main_layout = QVBoxLayout(card_widget)
        card_main_layout.setContentsMargins(20, 20, 20, 20)
        card_main_layout.setSpacing(15)

        # --- 顶部标题 ---
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title_label = QLabel("📚 参考文献国标刷")
        title_label.setStyleSheet(
            "font-family: 'Microsoft YaHei'; font-size: 20px; font-weight: bold; color: #2c3e50; border: none; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("杂乱格式/残缺文本  >>>  《GB/T 7714-2015》规范格式    |    点击结果可直达原文")
        subtitle_label.setStyleSheet("color: #7f8c8d; font-size: 12px; border: none; background: transparent;")
        subtitle_label.setAlignment(Qt.AlignCenter)

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        card_main_layout.addWidget(title_container)

        # --- 中间内容区 ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # 1. 左栏
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        lb_input = QLabel("📄 原文输入（每行一条文献）:")
        lb_input.setStyleSheet(
            "font-weight: bold; color: #34495e; font-size: 13px; border: none; background: transparent;")

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("在此粘贴多行参考文献...")
        # 调用支持透明样式的函数
        self.input_edit.setStyleSheet(self._get_editor_style(False))

        left_layout.addWidget(lb_input)
        left_layout.addWidget(self.input_edit)

        # 2. 中栏
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setAlignment(Qt.AlignCenter)

        self.btn_convert = QPushButton("国标刷 \n >>>")
        self.btn_convert.setFixedSize(80, 80)
        self.btn_convert.setCursor(Qt.PointingHandCursor)
        self.btn_convert.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3498db, stop:1 #2980b9);
                color: white; border-radius: 40px; font-size: 13px; font-weight: bold; border: 4px solid #f0f2f5;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5dade2, stop:1 #3498db); transform: scale(1.05); }
            QPushButton:pressed { background-color: #1f618d; padding-top: 3px; }
        """)
        middle_layout.addWidget(self.btn_convert)

        # 3. 右栏
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        # 顶部工具栏
        right_header_layout = QHBoxLayout()
        right_header_layout.setContentsMargins(0, 0, 0, 0)

        lb_output = QLabel("✅ 国标结果 (点击跳转):")
        lb_output.setStyleSheet(
            "font-weight: bold; color: #27ae60; font-size: 13px; border: none; background: transparent;")

        self.btn_copy_with_num = QPushButton("复制(含序号)")
        self.btn_copy_no_num = QPushButton("复制(纯净)")

        mini_btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.7); color: #27ae60; border: 1px solid #27ae60;
                border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #eafaf1; }
            QPushButton:pressed { background-color: #d5f5e3; padding-top: 1px; }
        """
        self.btn_copy_with_num.setStyleSheet(mini_btn_style)
        self.btn_copy_no_num.setStyleSheet(mini_btn_style)
        self.btn_copy_with_num.setEnabled(False)
        self.btn_copy_no_num.setEnabled(False)

        right_header_layout.addWidget(lb_output)
        right_header_layout.addStretch()
        right_header_layout.addWidget(self.btn_copy_with_num)
        right_header_layout.addWidget(self.btn_copy_no_num)

        # 【核心修改】这里改为 QTextBrowser，它才支持 setOpenExternalLinks
        self.output_edit = QTextBrowser()
        self.output_edit.setPlaceholderText("干净规整的参考文献即将出现...")

        # 允许打开外部链接
        self.output_edit.setOpenExternalLinks(True)
        # QTextBrowser 默认就是只读的，但写上也无妨
        self.output_edit.setReadOnly(True)

        # 调用支持透明样式的函数
        self.output_edit.setStyleSheet(self._get_editor_style(True))

        right_layout.addLayout(right_header_layout)
        right_layout.addWidget(self.output_edit)

        # 组装
        content_layout.addWidget(left_panel, 10)
        content_layout.addWidget(middle_panel, 2)
        content_layout.addWidget(right_panel, 10)
        card_main_layout.addLayout(content_layout)

        # --- 底部状态栏 ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; border: none; background: transparent;")

        self.last_result_label = QLabel("")
        self.last_result_label.setStyleSheet(
            "font-size: 11px; font-weight: bold; border: none; background: transparent;")

        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.last_result_label)

        card_main_layout.addLayout(bottom_layout)

        # --- 组装到主窗口 ---
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(15, 15, 15, 15)
        outer_layout.addWidget(card_widget)
        self.main_layout.addLayout(outer_layout)

    def _get_editor_style(self, is_read_only=False):
        """
        获取编辑器样式。
        【关键修改】:
        1. 使用 rgba 背景色以透出大卡片的模糊背景。
        2. 新增 'a' 标签样式：默认深灰色，悬停时变成蓝色下划线。
        3. 增加对 QTextBrowser 的支持。
        """
        if is_read_only:
            # 只读模式（右侧）：稍微灰一点
            bg_color = "rgba(249, 250, 252, 0.4)"
        else:
            # 编辑模式（左侧）：更通透的白色
            bg_color = "rgba(255, 255, 255, 0.4)"

        # 边框聚焦颜色
        border_focus = "#2ecc71" if is_read_only else "#3498db"
        bg_focus = "rgba(255, 255, 255, 0.9)"

        # 下面这行同时作用于 QTextEdit (输入框) 和 QTextBrowser (输出框)
        return f"""
            QTextEdit, QTextBrowser {{
                background-color: {bg_color}; 
                color: #2c3e50; 
                border: 1px solid rgba(220, 223, 230, 0.8);
                border-radius: 6px; 
                padding: 10px; 
                font-family: "Consolas", "Microsoft YaHei"; 
                font-size: 14px;
            }}
            QTextEdit:focus, QTextBrowser:focus {{ 
                border: 1px solid {border_focus}; 
                background-color: {bg_focus}; 
            }}
            /* 【链接样式美化】 */
            a {{
                color: #2c3e50;         /* 默认链接颜色：深灰 (看起来像普通文字) */
                text-decoration: none;  /* 去掉下划线 */
                font-weight: normal;
            }}
            a:hover {{
                color: #3498db;         /* 悬停时：变蓝 */
                text-decoration: underline; /* 悬停时：加下划线 */
                cursor: pointer;
            }}
        """

    def get_input_text(self):
        return self.input_edit.toPlainText().strip() if self.input_edit else ""

    def set_output_text(self, text):
        """设置纯文本 (旧接口保留)"""
        if self.output_edit: self.output_edit.setPlainText(text)

    def set_output_html(self, html_content):
        """
        【新增】设置 HTML 内容 (支持链接)
        """
        if self.output_edit:
            self.output_edit.setHtml(html_content)
```

---

### 📄 `views\__init__.py`

```python:views\__init__.py

```

---

### 📄 `workers\query_thread.py`

```python:workers\query_thread.py
"""
文件路径: workers/query_thread.py
=========================================================
【可用接口说明】

class QueryThread(QThread):
    # --- 信号 (用于通知界面) ---
    progress_signal = Signal(int, str)  # 进度信号 (百分比, 当前状态文本)
    finished_signal = Signal(str)       # 完成信号 (返回最终结果文本)
    error_signal = Signal(str)          # 错误信号 (返回错误信息)

    # --- 输入参数 ---
    def __init__(self, raw_text):
        '''初始化时传入用户输入的原始文本'''
        pass
=========================================================
"""

import sys
import os

# 路径修复
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtCore import QThread, Signal
from services.orchestrator import Orchestrator


class QueryThread(QThread):
    """
    工作线程。
    职责：在后台运行 Orchestrator，避免主界面卡死。
    """

    # 定义信号 (用来跟主界面喊话)
    # 信号必须定义在类变量里，不能在 __init__ 里
    progress_signal = Signal(int, str)  # 发送进度: (50, "正在查询第2条...")
    finished_signal = Signal(str)  # 发送结果: "Zhang San..."
    error_signal = Signal(str)  # 发送报错

    def __init__(self, raw_text):
        super().__init__()
        self.raw_text = raw_text
        self.orchestrator = Orchestrator()  # 实例化总指挥

    def run(self):
        """
        线程启动入口 (start()会自动调用此方法)。
        """
        try:
            if not self.raw_text.strip():
                self.error_signal.emit("输入内容为空！")
                return

            # 调用总指挥的批量处理方法
            # 把自己的 progress_signal 传进去，这样 orchestrator 就能实时汇报进度
            result_text = self.orchestrator.format_batch(
                self.raw_text,
                callback_signal=self.progress_signal
            )

            # 任务完成，发送结果
            self.finished_signal.emit(result_text)

        except Exception as e:
            # 万一崩溃，发送错误信号
            self.error_signal.emit(f"后台处理出错: {str(e)}")
```

---

### 📄 `workers\__init__.py`

```python:workers\__init__.py

```

---

