from PySide6.QtWidgets import (QDialogButtonBox, QDateTimeEdit, QDialog, QCalendarWidget)
from PySide6.QtCore import Qt, QDateTime, QTime

# === 1. 样式常量定义 ===

# 通用弹窗样式 (输入框、下拉菜单、滚动条修复)
DIALOG_STYLES = """
    QDialog { background-color: #ffffff; }
    QLabel { color: #2c3e50; font-size: 14px; font-weight: 600; font-family: "Microsoft YaHei"; }

    QLineEdit, QDoubleSpinBox, QDateTimeEdit, QTextEdit, QComboBox {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 6px 10px;
        background-color: #f9f9f9; 
        color: #333333;
        font-size: 14px;
        font-family: "Microsoft YaHei";
        min-height: 20px;
    }
    QLineEdit:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus, QTextEdit:focus, QComboBox:focus {
        background-color: #ffffff;
        border: 1px solid #3498db;
    }
    QLineEdit:read-only { background-color: #f0f0f0; color: #888; }

    /* 下拉菜单美化 */
    QComboBox::drop-down {
        border: none; background: transparent; width: 20px;
    }
    QComboBox QAbstractItemView {
        border: 1px solid #3498db;
        background-color: white;
        selection-background-color: #ecf5ff;
        selection-color: #3498db;
        outline: none;
        padding: 4px;
    }

    /* === 滚动条美化 (去除默认的丑陋背景) === */
    QScrollBar:vertical {
        border: none;
        background: #f9f9f9;
        width: 8px;
        margin: 0px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #dcdfe6;
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #c0c4cc;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

# 日历控件专属美化样式 (蓝色主题)
CALENDAR_STYLES = """
    /* 1. 整体背景和导航条 */
    QCalendarWidget QWidget#qt_calendar_navigationbar { 
        background-color: #3498db; 
        min-height: 35px;
    }
    QCalendarWidget QToolButton {
        color: white;
        background-color: transparent;
        border: none;
        font-weight: bold;
        icon-size: 20px;
        height: 30px;
    }
    QCalendarWidget QToolButton:hover {
        background-color: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }
    QCalendarWidget QToolButton::menu-indicator { image: none; }

    /* 2. 年份输入框和月份菜单 */
    QCalendarWidget QSpinBox {
        background-color: transparent;
        color: white;
        border: none;
        selection-background-color: rgba(255, 255, 255, 0.3);
        font-weight: bold;
    }
    QCalendarWidget QMenu { background-color: white; color: #333; border: 1px solid #ccc; }

    /* 3. 日期网格区域 */
    QCalendarWidget QAbstractItemView:enabled {
        background-color: white;
        color: #333;
        selection-background-color: #3498db; 
        selection-color: white;             
        font-family: "Microsoft YaHei";
        font-size: 13px;
        outline: none;
    }
    QCalendarWidget QAbstractItemView:disabled { color: #bbb; }
"""


# === 2. 工具函数 ===

def apply_dialog_theme(dialog: QDialog, button_box: QDialogButtonBox = None):
    """
    统一应用样式到对话框及其按钮
    """
    # 1. 应用 CSS
    dialog.setStyleSheet(DIALOG_STYLES)

    # 2. 如果传入了 button_box，专门美化确定/取消按钮
    if button_box:
        ok_btn = button_box.button(QDialogButtonBox.Ok)
        if ok_btn:
            ok_btn.setText("确定")
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #3498db; 
                    color: white; 
                    border: none; 
                    border-radius: 6px; 
                    padding: 8px 25px; 
                    font-weight: bold; 
                    font-size: 14px; 
                } 
                QPushButton:hover { background-color: #2980b9; }
            """)

        cancel_btn = button_box.button(QDialogButtonBox.Cancel)
        if cancel_btn:
            cancel_btn.setText("取消")
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #f1f2f6; 
                    color: #7f8c8d; 
                    border: none; 
                    border-radius: 6px; 
                    padding: 8px 25px; 
                    font-size: 14px; 
                } 
                QPushButton:hover { background-color: #e4e7eb; color: #2c3e50; }
            """)


def create_datetime_edit(init_dt=None, display_format="yyyy-MM-dd HH:mm"):
    """
    创建一个带有漂亮日历样式的日期时间选择器
    :param init_dt: 初始时间 (可以是字符串、QDateTime 或 None)
    :param display_format: 显示格式
    """
    dte = QDateTimeEdit()
    dte.setCalendarPopup(True)
    dte.setDisplayFormat(display_format)
    dte.setMinimumWidth(200)

    # 应用核心样式：对话框样式 + 日历样式
    dte.setStyleSheet(DIALOG_STYLES + CALENDAR_STYLES)

    # 时间初始化逻辑
    current = QDateTime.currentDateTime()
    # 默认设为整点，看起来整洁
    current.setTime(QTime(current.time().hour(), 0, 0))

    if init_dt:
        if isinstance(init_dt, str):
            # 尝试几种常见格式
            dt = QDateTime.fromString(init_dt, "yyyy-MM-dd HH:mm")
            if not dt.isValid():
                dt = QDateTime.fromString(init_dt, "yyyy-MM-dd-HH:00")  # 兼容你旧项目的格式

            if dt.isValid():
                dte.setDateTime(dt)
            else:
                dte.setDateTime(current)
        elif isinstance(init_dt, QDateTime):
            dte.setDateTime(init_dt)
    else:
        dte.setDateTime(current)

    return dte