import csv
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMenu)
from PySide6.QtCore import Qt, Signal

# Matplotlib 相关
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import rcParams

# 导入样式
from chart_styles import BTN_STYLE_NORMAL, BTN_STYLE_PRIMARY, TABLE_STYLE, MENU_STYLE

# 全局字体设置
rcParams['font.family'] = 'Microsoft YaHei'
rcParams['axes.unicode_minus'] = False
rcParams['font.size'] = 9


class BaseChartWidget(QWidget):
    """
    通用图表控件基类
    包含：Matplotlib 画布 + 底部/右侧数据表格 + 常用工具栏
    """
    # 信号：当数据被修改或文件被拖入时发射
    data_modified = Signal(list)
    file_dropped = Signal(str)

    def __init__(self, parent=None, show_table=True):
        super().__init__(parent)
        self.current_data = []  # 存储当前数据

        # 1. 布局初始化
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 2. 初始化 Matplotlib 画布
        self.fig = Figure(figsize=(5, 4), dpi=100, facecolor='white')
        # 调整边距，防止标签被遮挡
        self.fig.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.15)

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.ax = self.fig.add_subplot(111)

        # 【关键】修复滚动问题：强制忽略滚轮事件，防止与页面滚动冲突
        self.canvas.wheelEvent = lambda event: event.ignore()

        layout.addWidget(self.canvas, stretch=10)

        # 3. 工具栏区域
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 10, 0)

        # 预留左侧按钮槽（子类可以往这里加按钮）
        self.left_btn_layout = QHBoxLayout()
        btn_layout.addLayout(self.left_btn_layout)

        btn_layout.addStretch()

        # 右侧默认功能按钮
        self.btn_export_csv = QPushButton("📊 导出数据")
        self.btn_export_csv.setStyleSheet(BTN_STYLE_NORMAL)
        self.btn_export_csv.clicked.connect(self.export_csv)

        self.btn_export_img = QPushButton("🖼️ 导出图像")
        self.btn_export_img.setStyleSheet(BTN_STYLE_NORMAL)
        self.btn_export_img.clicked.connect(self.export_image)

        btn_layout.addWidget(self.btn_export_csv)
        btn_layout.addWidget(self.btn_export_img)
        layout.addLayout(btn_layout)

        # 4. 数据表格 (可选)
        if show_table:
            self.table = QTableWidget()
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["X 值", "Y 值"])  # 默认表头
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.verticalHeader().setVisible(False)
            self.table.setAlternatingRowColors(True)
            self.table.setStyleSheet(TABLE_STYLE)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            self.table.setMaximumHeight(150)

            # 右键菜单策略
            self.table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.table.customContextMenuRequested.connect(self.show_context_menu)

            layout.addWidget(self.table, stretch=3)

        # 初始化图表风格
        self._apply_chart_style()

    def _apply_chart_style(self):
        """应用美观的图表样式 (灰色边框、虚线网格)"""
        self.ax.clear()
        self.ax.set_facecolor('white')
        # 隐藏上、右边框
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        # 设置左、下边框颜色
        self.ax.spines['left'].set_color('#dcdfe6')
        self.ax.spines['bottom'].set_color('#dcdfe6')
        # 网格线设置
        self.ax.grid(True, linestyle=':', alpha=0.6, color='#909399')
        # 刻度线设置
        self.ax.tick_params(axis='both', which='both', direction='in',
                            length=4, width=1, color='#606266', labelcolor='#606266')

    def update_chart(self, x_data, y_data, title="图表标题", xlabel="X轴", ylabel="Y轴"):
        """
        子类直接调用此方法来刷新图表
        """
        self._apply_chart_style()  # 重置样式

        self.ax.set_title(title, fontsize=10, fontweight='bold', color='#303133', pad=10)
        self.ax.set_xlabel(xlabel, fontsize=9, color='#606266')
        self.ax.set_ylabel(ylabel, fontsize=9, color='#606266')

        # 绘制曲线
        self.ax.plot(x_data, y_data, color="#e74c3c", linewidth=2, label="Data")

        # 刷新画布
        self.canvas.draw()

        # 刷新表格 (如果有)
        if hasattr(self, 'table'):
            self._update_table(x_data, y_data)

    def _update_table(self, x_data, y_data):
        """内部方法：更新表格数据"""
        rows = min(len(x_data), 1000)  # 限制显示数量防止卡顿
        self.table.setRowCount(rows)
        self.table.setSortingEnabled(False)
        for i in range(rows):
            self.table.setItem(i, 0, QTableWidgetItem(f"{x_data[i]:.4f}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{y_data[i]:.4f}"))
        self.table.setSortingEnabled(True)

    def export_image(self):
        """通用导出图片功能"""
        file_path, _ = QFileDialog.getSaveFileName(self, "导出图片", "chart.png",
                                                   "PNG Image (*.png);;JPEG Image (*.jpg)")
        if file_path:
            try:
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", f"图片已保存:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def export_csv(self):
        """通用导出数据功能"""
        if not hasattr(self, 'table') or self.table.rowCount() == 0:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "导出数据", "data.csv", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    # 获取表头
                    headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                    writer.writerow(headers)
                    # 获取内容
                    for row in range(self.table.rowCount()):
                        row_data = []
                        for col in range(self.table.columnCount()):
                            item = self.table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                QMessageBox.information(self, "成功", f"数据已导出至:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def show_context_menu(self, pos):
        """表格右键菜单 (可重写)"""
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        menu.addAction("刷新图表", lambda: None)
        menu.exec(self.table.mapToGlobal(pos))