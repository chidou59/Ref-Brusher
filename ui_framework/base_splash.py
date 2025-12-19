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