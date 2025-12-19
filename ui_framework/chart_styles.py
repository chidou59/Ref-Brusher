# === 按钮样式 ===
BTN_STYLE_NORMAL = """
    QPushButton {
        background-color: white;
        border: 1px solid #dcdfe6;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        color: #606266;
    }
    QPushButton:hover {
        border-color: #409eff;
        color: #409eff;
        background-color: #ecf5ff;
    }
"""

BTN_STYLE_PRIMARY = """
    QPushButton {
        background-color: #e6f7ff;
        border: 1px solid #91d5ff;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        color: #1890ff;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1890ff;
        color: white;
    }
"""

BTN_STYLE_DANGER = """
    QPushButton {
        background-color: #fff0f0;
        border: 1px solid #ffccc7;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        color: #ff4d4f;
    }
    QPushButton:hover {
        background-color: #ff4d4f;
        color: white;
    }
"""

# === 表格样式 (带漂亮的表头和滚动条) ===
TABLE_STYLE = """
    QTableWidget {
        background-color: white;
        border: 1px solid #ebeef5;
        border-radius: 6px;
        gridline-color: #f2f6fc;
        font-size: 11px;
    }
    QHeaderView::section {
        background-color: #fafafe;
        color: #555;
        padding: 6px;
        border: none;
        border-bottom: 2px solid #e4e7ed;
        font-weight: bold;
        font-family: "Microsoft YaHei";
    }
    QTableWidget::item { padding: 4px; }
    QTableWidget::item:selected { background-color: #ecf5ff; color: #409eff; }

    /* 滚动条美化 */
    QScrollBar:vertical {
        border: none;
        background: #f4f6f9;
        width: 6px;
    }
    QScrollBar:handle:vertical {
        background: #c0c4cc;
        border-radius: 3px;
    }
"""

# === 右键菜单样式 ===
MENU_STYLE = """
    QMenu {
        background-color: #ffffff;
        border: 1px solid #f0f0f0;
        border-radius: 4px;
        padding: 4px 0px;
    }
    QMenu::item {
        background-color: transparent;
        color: #333333;
        padding: 6px 20px;
        margin: 2px 4px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #ecf5ff;
        color: #409eff;
    }
    QMenu::separator {
        height: 1px;
        background: #f0f0f0;
        margin: 4px 0px;
    }
"""