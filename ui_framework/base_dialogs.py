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