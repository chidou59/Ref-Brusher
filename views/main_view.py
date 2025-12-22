# views/main_view.py
# ==============================================================================
# 模块名称: 主界面视图 (View) - 布局修复版
# 修复内容:
#   1. 【重要】找回了消失的右侧标题和按钮（之前漏写了 addWidget）。
#   2. 保持了“✅ 国标输出...”的新文案和灰色链接样式。
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
        self.setWindowTitle("参考文献国标刷 v2.0")

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

        # 标题控件
        lb_output = QLabel("✅ 国标输出（点击即可前往原文）")
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

        # 【核心修复】将这些控件真正添加到布局中
        right_header_layout.addWidget(lb_output)
        right_header_layout.addStretch()
        right_header_layout.addWidget(self.btn_copy_with_num)
        right_header_layout.addWidget(self.btn_copy_no_num)

        # 输出框
        self.output_edit = QTextBrowser()
        self.output_edit.setPlaceholderText("干净规整的参考文献即将出现...")

        # 允许打开外部链接
        self.output_edit.setOpenExternalLinks(True)
        self.output_edit.setReadOnly(True)

        # 使用 setDefaultStyleSheet 设置默认链接样式
        self.output_edit.document().setDefaultStyleSheet(
            "a { color: #606266; text-decoration: none; font-weight: normal; }"
        )

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