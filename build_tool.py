"""
Available Interfaces:
- build_exe(): 主构建函数，执行自动化检查、安装依赖并调用 PyInstaller。
- get_resource_path(relative_path): 关键辅助函数，用于代码中获取图片等资源的绝对路径。
"""

import os
import sys
import subprocess
import shutil

# ==========================================
# 👇 用户配置区 (脚本会自动尝试识别，通常无需修改) 👇
# ==========================================

# 1. 软件名称 (默认取文件夹名字，也可手动改如 "MyApp")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.path.basename(BASE_DIR)

# 2. 入口文件 (默认寻找 main.py)
MAIN_FILE = "main.py"

# 3. 必须包含的单个文件 (如你的 background.jpg)
# 只要放在根目录下，这里写上文件名，打包工具就会把它塞进 exe
EXTRA_FILES = ["background.jpg"]

# 4. 资源文件夹 (如果有 assets 文件夹则保留，没有会自动跳过)
ASSETS_DIR_NAME = "assets"


# ==========================================
# 👆 配置结束 👆
# ==========================================

def get_resource_path(relative_path):
    """
    【重要】非科班同学请注意：
    在你的 main.py 中，加载图片的代码必须改为：
    img_path = get_resource_path("background.jpg")
    这样打包成 exe 后才能找到图片。
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def build_exe():
    print(f"🚀 启动通用打包工具...")
    os.chdir(BASE_DIR)  # 确保工作目录在脚本所在位置

    # 1. 环境准备：安装依赖
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        print(f"📦 检测到 {req_file}，正在检查/安装依赖库...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        except Exception as e:
            print(f"⚠️ 安装依赖失败，请检查网络或 pip 环境: {e}")

    # 安装 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("⚠️ 正在安装打包核心组件 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pyinstaller])

    # 2. 自动搜寻图标 (.ico)
    icon_file = ""
    for file in os.listdir(BASE_DIR):
        if file.endswith(".ico"):
            icon_file = file
            print(f"🎨 自动发现图标文件: {icon_file}")
            break

    # 3. 确认入口文件
    if not os.path.exists(MAIN_FILE):
        print(f"❌ 错误：在当前目录找不到 {MAIN_FILE}！")
        return

    # 4. 选择模式
    print("\n请选择打包模式：")
    print("1. 单文件 (.exe) - 方便传给别人，启动稍慢")
    print("2. 文件夹 (目录) - 启动极快，适合专业软件")
    choice = input("请输入 1 或 2 [默认1]: ").strip()
    mode_arg = "--onedir" if choice == "2" else "--onefile"

    # 5. 构建命令
    cmd = [
        "pyinstaller",
        "--noconsole",  # 不显示黑窗口
        "--clean",  # 打包前清理临时文件
        mode_arg,
        f'--name={APP_NAME}',
    ]

    # 添加图标
    if icon_file:
        cmd.append(f'--icon={icon_file}')

    # 添加 background.jpg 等单文件
    for f in EXTRA_FILES:
        if os.path.exists(f):
            # 格式：--add-data "源文件;打包后路径" (Windows用分号)
            cmd.append(f'--add-data="{f};."')
            print(f"🖼️ 已添加额外资源: {f}")

    # 添加 assets 文件夹
    if os.path.exists(ASSETS_DIR_NAME):
        cmd.append(f'--add-data="{ASSETS_DIR_NAME};{ASSETS_DIR_NAME}"')
        print(f"📂 已添加文件夹: {ASSETS_DIR_NAME}")

    cmd.append(MAIN_FILE)

    # 6. 执行打包
    full_command = " ".join(cmd)
    print("\n" + "=" * 50)
    print(f"🛠️ 正在执行: {full_command}")
    print("=" * 50 + "\n")

    os.system(full_command)

    # 7. 善后
    if os.path.exists("dist"):
        print(f"\n✅ 打包任务完成！请查看 dist 文件夹。")
        os.startfile("dist")


if __name__ == "__main__":
    build_exe()