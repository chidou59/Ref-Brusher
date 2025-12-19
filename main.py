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
        self.view.set_output_text("")
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