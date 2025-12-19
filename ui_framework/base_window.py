import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QLabel, QSizePolicy, QApplication)
from PySide6.QtGui import (QAction, QColor, QPixmap, QPainter,
                           QGuiApplication)
from PySide6.QtCore import Qt, QSize


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

        # 【修改】路径改为根目录下的 background.jpg
        # 假设程序是从根目录运行的 (python main.py)，直接使用文件名即可
        bg_path = "background.jpg"

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
            # 【修改】将不透明度设置为 0.06
            painter.setOpacity(0.15)

            # 保持比例铺满窗口
            scaled_pixmap = self.bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)

        painter.setOpacity(1.0)