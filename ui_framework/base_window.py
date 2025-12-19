"""
文件路径: ui_framework/base_window.py
=========================================================
【可用接口说明】

class BaseMainWindow(QMainWindow):
    # 1. paintEvent(event): 自动处理背景图绘制逻辑 (0.15 不透明度)
    # 2. resizeEvent(event): 处理窗口缩放时右下角签名的定位
    # 3. setWindowIcon(): 启动时加载根目录下的 Brush.ico
=========================================================
"""

import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QLabel, QSizePolicy, QApplication)
from PySide6.QtGui import (QColor, QPixmap, QPainter, QGuiApplication, QIcon)
from PySide6.QtCore import Qt


class BaseMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置默认标题
        self.setWindowTitle("Ref-Brusher | 文献国标刷")

        # --- 设置窗口图标 ---
        # 直接读取根目录下的图标文件
        icon_path = "Brush.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

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
        bg_path = "background.jpg"

        if os.path.exists(bg_path):
            self.bg_pixmap = QPixmap(bg_path)
        else:
            print(f"⚠️ 未找到背景图: {bg_path} (请确保图片位于项目根目录)")

        # === 3. 左下角签名 ===
        self.signature_label = QLabel("@小白元宵", self)
        self.signature_label.setStyleSheet("""
            color: rgba(100, 100, 100, 150); 
            font-family: 'Microsoft YaHei'; 
            font-size: 11px; 
            font-weight: bold;
            background: transparent;
        """)
        self.signature_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.signature_label.adjustSize()

        # === 4. 中央主区域 ===
        self.central_widget = QWidget()
        self.central_widget.setAttribute(Qt.WA_TranslucentBackground)  # 必须透明
        self.setCentralWidget(self.central_widget)

        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)

    # === 事件处理 ===
    def resizeEvent(self, event):
        """当窗口大小改变时，重新定位签名标签"""
        super().resizeEvent(event)
        if hasattr(self, 'signature_label'):
            # 定位在左下角，留一点边距
            self.signature_label.move(10, self.height() - self.signature_label.height() - 5)
            self.signature_label.raise_()

    def paintEvent(self, event):
        """绘制窗口背景色及半透明背景图"""
        painter = QPainter(self)

        # 绘制背景色 (淡蓝灰)
        painter.fillRect(self.rect(), QColor("#f0f2f5"))

        # 绘制背景图
        if self.show_bg_image and self.bg_pixmap and not self.bg_pixmap.isNull():
            # 设置不透明度为 0.15
            painter.setOpacity(0.15)

            # 保持比例铺满窗口
            scaled_pixmap = self.bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)

        painter.setOpacity(1.0)