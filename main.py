# main.py
# ==============================================================================
# 模块名称: 主程序入口 - 复制逻辑优化版
# 功能描述:
#   1. 修复复制时多余空行的问题 (界面显示空行，复制时自动去除)
# ==============================================================================

import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
from PySide6.QtCore import QThread, Signal, QObject

from views.main_view import MainView
from services.orchestrator import Orchestrator


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
        self.view = MainView()
        self.view.setup_ui()
        self.orchestrator = Orchestrator()
        self.worker = None
        self.current_results = {"with_num": "", "no_num": ""}
        self.connect_signals()
        self.view.show()

    def connect_signals(self):
        if self.view.btn_convert:
            self.view.btn_convert.clicked.connect(self.start_batch_processing)
        if self.view.btn_copy_with_num:
            self.view.btn_copy_with_num.clicked.connect(self.copy_result_with_num)
        if self.view.btn_copy_no_num:
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
        """复制带序号文本 (自动去除界面显示用的额外空行)"""
        text = self.current_results.get("with_num", "")
        if text:
            # 【关键修改】把双换行替换回单换行，实现紧凑复制
            clean_text = text.replace("\n\n", "\n")
            QApplication.clipboard().setText(clean_text)
            self.view.status_label.setText("📋 已复制 (带序号)")

    def copy_result_no_num(self):
        """复制无序号文本 (自动去除界面显示用的额外空行)"""
        text = self.current_results.get("no_num", "")
        if text:
            # 【关键修改】把双换行替换回单换行
            clean_text = text.replace("\n\n", "\n")
            QApplication.clipboard().setText(clean_text)
            self.view.status_label.setText("📋 已复制 (纯净版)")

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    controller = RefFormatterController()
    controller.run()