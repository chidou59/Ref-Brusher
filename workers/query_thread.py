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