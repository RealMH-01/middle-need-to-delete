# -*- coding: utf-8 -*-
"""历史记录页

本轮新增：
- 每行新增「详情」「以此新建」两个按钮（位于最后的"操作"列）
- 「详情」弹出完整的创建结果（包含新建/跳过/复制的文件夹与文件清单）
- 「以此新建」通过 :pyattr:`request_reuse` 信号通知主窗口跳转到单笔创建页，
  并用本条记录的业务员/客户/订单类型/产品类别预填表单
- 旧的历史记录（没有 ``detail`` 字段）不会报错，只显示统计数字
"""

import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QHeaderView, QLabel,
                              QLineEdit, QMessageBox, QPlainTextEdit,
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QVBoxLayout, QWidget)


COLS = [
    ("time", "操作时间", 150),
    ("operator", "操作人", 100),
    ("salesperson", "业务员", 100),
    ("customer", "客户", 160),
    ("order_no", "订单号", 160),
    ("order_type", "订单类型", 80),
    ("product_category", "产品类别", 90),
    ("template_name", "模板", 200),
    ("path", "路径", 300),
    ("result", "结果", 140),
    ("_ops", "操作", 200),  # 新增：操作列（详情 + 以此新建）
]

# 路径列索引（供打开选中订单文件夹使用）
_PATH_COL = next(i for i, c in enumerate(COLS) if c[0] == "path")
# 操作列索引
_OPS_COL = next(i for i, c in enumerate(COLS) if c[0] == "_ops")


class HistoryPage(QWidget):
    request_back = pyqtSignal()
    # 新增：请求以某条历史记录为基础快速新建订单
    request_reuse = pyqtSignal(dict)

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self._all_records = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 14)
        root.setSpacing(10)

        top = QHBoxLayout()
        btn_back = QPushButton("← 返回首页")
        btn_back.setObjectName("SecondaryButton")
        btn_back.clicked.connect(self.request_back.emit)
        top.addWidget(btn_back)
        title = QLabel("历史记录")
        title.setObjectName("TitleLabel")
        top.addWidget(title)
        top.addStretch(1)
        root.addLayout(top)

        # 搜索
        sh = QHBoxLayout()
        sh.addWidget(QLabel("搜索："))
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("按订单号 / 业务员 / 客户过滤")
        self.edit_search.textChanged.connect(self._apply_filter)
        sh.addWidget(self.edit_search, 1)
        btn_open = QPushButton("打开选中订单文件夹")
        btn_open.setObjectName("SecondaryButton")
        btn_open.clicked.connect(self._open_selected)
        btn_refresh = QPushButton("刷新")
        btn_refresh.setObjectName("SecondaryButton")
        btn_refresh.clicked.connect(self.refresh)
        sh.addWidget(btn_open)
        sh.addWidget(btn_refresh)
        root.addLayout(sh)

        # 表格
        self.table = QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels([c[1] for c in COLS])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        for i, (_, _, w) in enumerate(COLS):
            self.table.setColumnWidth(i, w)
        root.addWidget(self.table, 1)

    def refresh(self):
        self._all_records = self.storage.load_history()
        # 已按 insert 顺序最新在前
        self._apply_filter()

    def _apply_filter(self):
        kw = self.edit_search.text().strip().lower()
        records = self._all_records
        if kw:
            records = [r for r in records if
                       kw in str(r.get("order_no", "")).lower() or
                       kw in str(r.get("salesperson", "")).lower() or
                       kw in str(r.get("customer", "")).lower()]
        self.table.setRowCount(0)
        for rec in records:
            r = self.table.rowCount()
            self.table.insertRow(r)
            result_txt = rec.get("result", "")
            if "成功" in result_txt:
                detail = (
                    f"{result_txt}（新建 {rec.get('created_count', 0)}，"
                    f"跳过 {rec.get('skipped_count', 0)}，"
                    f"复制 {rec.get('copied_count', 0)}）"
                )
            else:
                detail = result_txt
            for ci, (k, _, _) in enumerate(COLS):
                if k == "_ops":
                    continue  # 操作列由 cellWidget 填充
                v = detail if k == "result" else str(rec.get(k, ""))
                self.table.setItem(r, ci, QTableWidgetItem(v))
            # 操作列：详情 + 以此新建
            self._attach_ops_widget(r, rec)

    def _attach_ops_widget(self, row_index: int, record: dict):
        """在表格行的"操作"列放一个包含两个按钮的小组件。"""
        ops_widget = QWidget()
        ops_layout = QHBoxLayout(ops_widget)
        ops_layout.setContentsMargins(4, 2, 4, 2)
        ops_layout.setSpacing(6)

        btn_detail = QPushButton("详情")
        btn_detail.setObjectName("SecondaryButton")
        btn_detail.setFixedHeight(28)
        btn_detail.clicked.connect(
            lambda checked=False, r=record: self._show_detail(r)
        )

        btn_reuse = QPushButton("以此新建")
        btn_reuse.setObjectName("SecondaryButton")
        btn_reuse.setFixedHeight(28)
        btn_reuse.clicked.connect(
            lambda checked=False, r=record: self._reuse_record(r)
        )

        ops_layout.addWidget(btn_detail)
        ops_layout.addWidget(btn_reuse)
        ops_widget.setLayout(ops_layout)
        self.table.setCellWidget(row_index, _OPS_COL, ops_widget)

    def _show_detail(self, record: dict):
        """弹窗显示历史记录的完整信息。

        对老记录（没有 ``detail`` 字段）做兼容——只显示统计数字。
        """
        dlg = QDialog(self)
        dlg.setWindowTitle(f"创建详情 - {record.get('order_no', '')}")
        dlg.resize(680, 520)
        v = QVBoxLayout(dlg)

        # 基本信息
        info_lines = [
            f"订单号：{record.get('order_no', '')}",
            f"客户：{record.get('customer', '')}",
            f"业务员：{record.get('salesperson', '')}",
            f"订单类型：{record.get('order_type', '')}",
            f"产品类别：{record.get('product_category', '') or '（未设置）'}",
            f"模板：{record.get('template_name', '')}",
            f"创建时间：{record.get('time', '')}",
            f"路径：{record.get('path', '')}",
            "",
            f"新建文件夹数：{record.get('created_count', 0)}",
            f"跳过已存在：{record.get('skipped_count', 0)}",
            f"复制模板文件：{record.get('copied_count', 0)}",
        ]

        detail = record.get("detail") or {}
        if detail:
            info_lines.append("")
            created = detail.get("created", []) or []
            skipped = detail.get("skipped", []) or []
            copy_results = detail.get("copy_results", []) or []
            if created:
                info_lines.append("--- 新建的文件夹 ---")
                for p in created:
                    info_lines.append(f"  + {p}")
            if skipped:
                info_lines.append("")
                info_lines.append("--- 跳过的文件夹（已存在）---")
                for p in skipped:
                    info_lines.append(f"  · {p}")
            if copy_results:
                copied = [r for r in copy_results if r.get("copied")]
                failed = [r for r in copy_results if not r.get("copied")]
                if copied:
                    info_lines.append("")
                    info_lines.append("--- 复制的模板文件 ---")
                    for r in copied:
                        dst = r.get("dst", "")
                        src = r.get("src", "")
                        info_lines.append(
                            f"  + {os.path.basename(dst) if dst else ''}"
                            f"{'  ← ' + src if src else ''}"
                        )
                if failed:
                    info_lines.append("")
                    info_lines.append("--- 未复制的模板文件 ---")
                    for r in failed:
                        info_lines.append(
                            f"  · {r.get('src', '')}  原因：{r.get('reason', '')}"
                        )
        else:
            info_lines.append("")
            info_lines.append(
                "（老版本生成的历史记录没有保存详细清单，这里只能看到统计数字。）"
            )

        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText("\n".join(info_lines))
        v.addWidget(text, 1)

        btn_close = QPushButton("关闭")
        btn_close.setObjectName("SecondaryButton")
        btn_close.clicked.connect(dlg.accept)
        h = QHBoxLayout()
        h.addStretch(1)
        h.addWidget(btn_close)
        v.addLayout(h)

        dlg.exec_()

    def _reuse_record(self, record: dict):
        """以历史记录为基础，跳转到单笔创建页并预填数据。"""
        self.request_reuse.emit(record)

    def _open_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "提示", "请选择一行")
            return
        row = rows[0].row()
        path_item = self.table.item(row, _PATH_COL)
        if not path_item:
            return
        path = path_item.text()
        if not os.path.isdir(path):
            QMessageBox.warning(self, "提示", "目录不存在（可能已被移动或删除）")
            return
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif os.name == "posix":
                import subprocess
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
