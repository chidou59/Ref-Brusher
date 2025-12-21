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