# -*- coding: utf-8 -*-
"""批量导入页 —— Neo-brutalism 视觉适配 + StyledComboBox 替换。

本轮改造（不动业务逻辑）：
- 顶部栏新增 "❓帮助" 按钮，发出 :pyattr:`request_help` 信号，让
  主窗口打开帮助 DockWidget 并跳转到批量导入章节；
- 身份区与每行产品类别、订单类型下拉框改用
  :class:`app.widgets.styled_combo.StyledComboBox`（业务员/客户可搜索）；
- 产品类别在 ``origin_map`` 为空时整列隐藏，但列索引保持不变，以兼容
  现有测试与数据流；:meth:`_collect_rows` 在列隐藏时返回空串；
- Excel 导入完成后，对每行业务员做一次系统校验，找不到的行以
  黄色背景高亮提示（**警告级**，不阻断导入）；
- 按钮调整为 Neo-brutalism 风格（主按钮默认强调色，次按钮灰体黑边）。
"""

import os
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import (
    QCheckBox, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

from ..core import folder_builder
from ..style import COLOR_SECONDARY
from ..widgets import StyledComboBox


HEADERS = ["订单类型", "订单号", "客户名称", "产品信息", "客户PO号", "产品类别", "是否商检", "状态"]

# 黄色警告背景（异常业务员行高亮用）
_WARN_BG = QColor(COLOR_SECONDARY)  # #FFD93D
_WARN_FG = QColor("#000000")


class BatchPage(QWidget):
    request_back = pyqtSignal()
    # 顶部"❓帮助"按钮：让主窗口打开帮助 DockWidget 并跳转到批量章节
    request_help = pyqtSignal(str)

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self._build_ui()

    # ============== UI ==============
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 14)
        root.setSpacing(10)

        # ------ 顶部栏 ------
        top = QHBoxLayout()
        btn_back = QPushButton("← 返回首页")
        btn_back.setObjectName("SecondaryButton")
        btn_back.clicked.connect(self.request_back.emit)
        top.addWidget(btn_back)
        title = QLabel("批量导入")
        title.setObjectName("TitleLabel")
        top.addWidget(title)
        top.addStretch(1)

        # ❓ 帮助按钮 —— 打开右侧帮助 Dock，定位到"批量导入"章节
        btn_help = QPushButton("❓ 帮助")
        btn_help.setObjectName("SecondaryButton")
        btn_help.setToolTip("打开右侧帮助面板，查看批量导入的详细说明")
        btn_help.clicked.connect(lambda: self.request_help.emit("sec-batch"))
        top.addWidget(btn_help)

        root.addLayout(top)

        # ----- 身份与模板 -----
        id_group = QGroupBox("① 身份与模板（批量订单共用）")
        id_layout = QGridLayout(id_group)
        id_layout.addWidget(QLabel("业务员："), 0, 0)
        self.cmb_sales = StyledComboBox(searchable=True)
        self.cmb_sales.setMinimumWidth(180)
        id_layout.addWidget(self.cmb_sales, 0, 1)
        id_layout.addWidget(QLabel("客户（可留空，使用每行的客户名称）："), 0, 2)
        self.cmb_customer = StyledComboBox(searchable=True)
        self.cmb_customer.setMinimumWidth(200)
        id_layout.addWidget(self.cmb_customer, 0, 3)
        tip = QLabel(
            "提示：批量导入时，模板按「订单类型 + 业务员 + 客户」自动匹配；"
            "若 Excel 中「业务员」列在系统中不存在，对应行会被"
            "<span style='background:#FFD93D;color:#000;padding:0 4px;'>"
            "黄色警告</span>标记。"
        )
        tip.setStyleSheet("color:#000000;")
        tip.setWordWrap(True)
        tip.setTextFormat(Qt.RichText)
        id_layout.addWidget(tip, 1, 0, 1, 4)
        self.cmb_sales.currentIndexChanged.connect(self._reload_customers)
        root.addWidget(id_group)

        # ----- 导入方式 -----
        op_group = QGroupBox("② 导入订单")
        op_layout = QHBoxLayout(op_group)
        btn_dl = QPushButton("下载 Excel 模板")
        btn_dl.setObjectName("SecondaryButton")
        btn_dl.clicked.connect(self._download_template)
        btn_import = QPushButton("导入 Excel")
        btn_import.clicked.connect(self._import_excel)
        btn_add = QPushButton("＋ 添加一行")
        btn_add.setObjectName("SecondaryButton")
        btn_add.clicked.connect(lambda: self._add_row())
        btn_del = QPushButton("－ 删除选中行")
        btn_del.setObjectName("SecondaryButton")
        btn_del.clicked.connect(self._del_rows)
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 200)
        self.spin_rows.setValue(5)
        btn_gen = QPushButton("按预设行数生成")
        btn_gen.setObjectName("SecondaryButton")
        btn_gen.clicked.connect(self._gen_rows)

        op_layout.addWidget(btn_dl)
        op_layout.addWidget(btn_import)
        op_layout.addSpacing(20)
        op_layout.addWidget(btn_add)
        op_layout.addWidget(btn_del)
        op_layout.addSpacing(20)
        op_layout.addWidget(QLabel("预设行数："))
        op_layout.addWidget(self.spin_rows)
        op_layout.addWidget(btn_gen)
        op_layout.addStretch(1)
        root.addWidget(op_group)

        # ----- 表格 -----
        self.table = QTableWidget(0, len(HEADERS) + 1)  # +1 for 序号
        all_headers = ["序号"] + HEADERS
        self.table.setHorizontalHeaderLabels(all_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 列宽：序号 50, 订单类型 80, 订单号 180, 客户名称 180, 产品信息 160,
        #      客户PO号 140, 产品类别 100, 是否商检 80, 状态 220
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 180)
        self.table.setColumnWidth(4, 160)
        self.table.setColumnWidth(5, 140)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 80)
        self.table.setColumnWidth(8, 220)
        root.addWidget(self.table, 1)

        # ----- 执行 -----
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        btn_preview = QPushButton("预览全部")
        btn_preview.setObjectName("SecondaryButton")
        btn_preview.clicked.connect(self._preview_all)
        btn_run = QPushButton("确认批量创建")
        # 主按钮：Neo-brutalism 主色 + 加粗强调
        btn_run.setStyleSheet("font-size:14px; font-weight:bold; padding:8px 24px;")
        btn_run.clicked.connect(self._run_all)
        bottom.addWidget(btn_preview)
        bottom.addWidget(btn_run)
        root.addLayout(bottom)

    # ============== 外部入口 ==============
    def refresh(self):
        self._load_salespersons()
        # 根据 origin_map 决定是否隐藏产品类别列（列索引保持不变）
        self._refresh_category_column_visibility()

    # ============== 数据 ==============
    def _load_salespersons(self):
        self.cmb_sales.blockSignals(True)
        self.cmb_sales.clear()
        names = [it["name"] for it in self.storage.load_salespersons()]
        self.cmb_sales.addItems([""] + names)
        self.cmb_sales.blockSignals(False)
        self._reload_customers()

    def _reload_customers(self):
        sales = self.cmb_sales.currentText()
        self.cmb_customer.clear()
        if sales:
            self.cmb_customer.addItems([""] + self.storage.get_customers(sales))
        else:
            self.cmb_customer.addItems([""])

    def _refresh_category_column_visibility(self):
        """``origin_map`` 为空时隐藏"产品类别"列（索引 6）。

        列索引保持不变，以便既有的 ``_collect_rows``、单测逻辑依然
        使用 ``cellWidget(r, 6)`` 访问；隐藏时不会影响功能，只是
        用户看不到该列，且 ``_collect_rows`` 在此情况下返回空串。
        """
        cfg = self.storage.load_config() if self.storage else {}
        has_cats = bool(cfg.get("origin_map") or {})
        # 列 6 = 产品类别
        self.table.setColumnHidden(6, not has_cats)

    # ============== 表格操作 ==============
    def _add_row(self, data=None):
        """data: dict 可预填"""
        r = self.table.rowCount()
        self.table.insertRow(r)
        # 序号
        it = QTableWidgetItem(str(r + 1))
        it.setFlags(it.flags() & ~Qt.ItemIsEditable)
        it.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(r, 0, it)

        # 订单类型 StyledComboBox
        cmb_type = StyledComboBox()
        cmb_type.addItems(["外贸", "内贸"])
        if data and data.get("order_type") in ("外贸", "内贸"):
            cmb_type.setCurrentText(data["order_type"])
        self.table.setCellWidget(r, 1, cmb_type)

        # 订单号（per-row 业务员存入该单元格的 UserRole，供 _collect_rows 使用）
        no_item = QTableWidgetItem(data.get("order_no", "") if data else "")
        per_row_sp = (data.get("salesperson") or "").strip() if data else ""
        no_item.setData(Qt.UserRole, per_row_sp)
        self.table.setItem(r, 2, no_item)
        # 客户
        self.table.setItem(r, 3, QTableWidgetItem(data.get("customer", "") if data else ""))
        # 产品信息
        self.table.setItem(r, 4, QTableWidgetItem(data.get("product_info", "") if data else ""))

        # 客户PO号
        self.table.setItem(r, 5, QTableWidgetItem(data.get("po_no", "") if data else ""))

        # 产品类别（从 config.json 的 origin_map 动态读取；列可能被隐藏）
        cmb_cat = StyledComboBox(searchable=True)
        cfg = self.storage.load_config() if self.storage else {}
        category_options = list((cfg.get("origin_map") or {}).keys())
        if category_options:
            cmb_cat.addItems(category_options)
        if data and data.get("product_category") in category_options:
            cmb_cat.setCurrentText(data["product_category"])
        self.table.setCellWidget(r, 6, cmb_cat)

        # 是否商检
        chk = QCheckBox()
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        lay.addWidget(chk)
        if data and data.get("needs_inspection"):
            chk.setChecked(True)
        self.table.setCellWidget(r, 7, w)

        # 状态
        self.table.setItem(r, 8, QTableWidgetItem(""))

        self._renumber()

    def _del_rows(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "提示", "请选中要删除的行")
            return
        for r in rows:
            self.table.removeRow(r)
        self._renumber()

    def _gen_rows(self):
        self.table.setRowCount(0)
        for _ in range(self.spin_rows.value()):
            self._add_row()

    def _renumber(self):
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 0)
            if it:
                it.setText(str(r + 1))

    # ============== Excel ==============
    def _download_template(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存 Excel 模板", "批量导入模板.xlsx", "Excel 文件 (*.xlsx)")
        if not path:
            return
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = Workbook()
        ws = wb.active
        ws.title = "批量导入"
        headers = ["订单类型", "订单号", "客户名称", "产品信息", "客户PO号",
                   "产品类别", "是否需要商检", "业务员"]
        ws.append(headers)
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=c)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2196F3")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        # 示例（业务员列为空时，使用页面顶部选择的业务员）
        # 产品类别示例取 config.json 中 origin_map 的第一个 key（保持与当前配置一致）
        cfg_sample = self.storage.load_config() if self.storage else {}
        sample_category = ""
        om_sample = cfg_sample.get("origin_map") or {}
        if om_sample:
            sample_category = next(iter(om_sample.keys()))
        ws.append(["外贸", "EXP-2026001", "示例客户A", "产品示例 200KG",
                   "PO-2026-001", sample_category, "是", "示例业务员"])
        ws.append(["内贸", "DOM-2026002", "示例客户B", "产品示例 1T",
                   "", sample_category, "否", ""])
        widths = [12, 22, 24, 28, 18, 12, 14, 12]
        from openpyxl.utils import get_column_letter
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
        wb.save(path)
        QMessageBox.information(self, "成功", f"模板已保存到：\n{path}")

    def _import_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Excel 文件", "", "Excel 文件 (*.xlsx *.xls)")
        if not path:
            return
        try:
            from openpyxl import load_workbook
            wb = load_workbook(path, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                QMessageBox.warning(self, "提示", "Excel 为空")
                return
            header = [str(x).strip() if x else "" for x in rows[0]]
            def idx(name):
                for i, h in enumerate(header):
                    if name in h:
                        return i
                return -1
            i_type = idx("订单类型")
            i_no = idx("订单号")
            i_cust = idx("客户名称")
            i_prod = idx("产品信息")
            i_po = idx("PO号")
            i_cat = idx("产品类别")
            i_insp = idx("商检")
            i_sp = idx("业务员")

            # 合法的产品类别列表从 config.json 的 origin_map 动态读取
            cfg_import = self.storage.load_config() if self.storage else {}
            valid_categories = list((cfg_import.get("origin_map") or {}).keys())
            # fallback 默认值：origin_map 的第一个 key（若有），否则空串
            default_category = valid_categories[0] if valid_categories else ""

            # 系统中所有业务员名单，用于校验 Excel 中的"业务员"列
            known_salespersons = {
                it["name"] for it in self.storage.load_salespersons()
            }
            # 记录本次导入时"在系统中找不到"的行索引（以本次插入后的 row 号为准）
            invalid_rows = []
            invalid_names = []

            # 本次导入的起点行号（追加模式）
            start_row = self.table.rowCount()

            count = 0
            for r in rows[1:]:
                if not r or all(x is None or str(x).strip() == "" for x in r):
                    continue
                data = {
                    "order_type": (str(r[i_type]).strip() if i_type >= 0 and r[i_type] else "外贸"),
                    "order_no": (str(r[i_no]).strip() if i_no >= 0 and r[i_no] else ""),
                    "customer": (str(r[i_cust]).strip() if i_cust >= 0 and r[i_cust] else ""),
                    "product_info": (str(r[i_prod]).strip() if i_prod >= 0 and r[i_prod] else ""),
                    "po_no": (str(r[i_po]).strip() if i_po >= 0 and r[i_po] else ""),
                    "product_category": (str(r[i_cat]).strip() if i_cat >= 0 and r[i_cat] else default_category),
                    "salesperson": (str(r[i_sp]).strip() if i_sp >= 0 and r[i_sp] else ""),
                }
                if valid_categories and data["product_category"] not in valid_categories:
                    data["product_category"] = default_category
                if data["order_type"] not in ("外贸", "内贸"):
                    data["order_type"] = "外贸"
                insp_raw = str(r[i_insp]).strip() if i_insp >= 0 and r[i_insp] is not None else ""
                data["needs_inspection"] = insp_raw in ("是", "Y", "y", "YES", "yes", "1", "true", "True", "✓")

                # 每行业务员校验（Excel 写了、但系统里没有）
                per_row_sp = data["salesperson"].strip()
                row_invalid = bool(per_row_sp) and per_row_sp not in known_salespersons

                self._add_row(data)
                new_row_idx = self.table.rowCount() - 1
                if row_invalid:
                    invalid_rows.append(new_row_idx)
                    invalid_names.append(per_row_sp)
                    self._mark_row_warning(
                        new_row_idx,
                        f"⚠ 业务员「{per_row_sp}」未在系统中找到，请先新增或用扫描导入",
                    )
                count += 1

            # 汇总提示
            if invalid_rows:
                uniq_names = sorted(set(invalid_names))
                preview = "、".join(uniq_names[:10])
                if len(uniq_names) > 10:
                    preview += "…"
                QMessageBox.warning(
                    self, "导入完成（含警告）",
                    f"已导入 {count} 行，其中 {len(invalid_rows)} 行业务员在系统中未找到：\n"
                    f"{preview}\n\n"
                    "这些行已用<黄色>背景高亮，可在执行前到首页"
                    "「🧭 扫描导入业务员」或手动添加业务员后再批量创建。"
                )
            else:
                QMessageBox.information(self, "成功", f"已导入 {count} 行。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解析 Excel 失败：{e}")

    def _mark_row_warning(self, row: int, status_text: str = ""):
        """将整行背景设为警告黄色，并在状态列写入提示。"""
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item is not None:
                item.setBackground(QBrush(_WARN_BG))
                item.setForeground(QBrush(_WARN_FG))
        if status_text:
            it = QTableWidgetItem(status_text)
            it.setBackground(QBrush(_WARN_BG))
            it.setForeground(QBrush(_WARN_FG))
            self.table.setItem(row, 8, it)

    # ============== 采集 ==============
    def _collect_rows(self):
        rows = []
        common_sales = self.cmb_sales.currentText().strip()

        # Bug 12 修复：顶部的"共用业务员"是 searchable 下拉框，用户可能只输入了
        # 部分文字而未从下拉列表中点选。这种情况下 currentText() 返回的是无效文本，
        # 会导致后续每一行订单的路径拼接出错。对共用业务员做阻断式校验。
        # 注意：cmb_sales 的第一项是空字符串（允许不选，按每行 per_row_sp 使用），
        # 所以空串是合法的，不需要阻断。
        if common_sales and self.cmb_sales.findText(common_sales) < 0:
            QMessageBox.warning(
                self, "提示",
                f"业务员「{common_sales}」不在列表中，请从下拉列表中选择。"
            )
            return []

        # Bug 12 修复：同样对"共用客户"做阻断式校验（空串合法）。
        common_customer = self.cmb_customer.currentText().strip()
        if common_customer and self.cmb_customer.findText(common_customer) < 0:
            QMessageBox.warning(
                self, "提示",
                f"客户「{common_customer}」不在列表中，请从下拉列表中选择。"
            )
            return []

        # 产品类别列是否可见？不可见时统一返回空串
        cat_col_hidden = self.table.isColumnHidden(6)
        for r in range(self.table.rowCount()):
            order_type = self.table.cellWidget(r, 1).currentText()
            no_item = self.table.item(r, 2)
            order_no = no_item.text().strip() if no_item else ""
            per_row_sp = (no_item.data(Qt.UserRole) if no_item else "") or ""
            customer = self.table.item(r, 3).text().strip() if self.table.item(r, 3) else ""
            product_info = self.table.item(r, 4).text().strip() if self.table.item(r, 4) else ""
            po_no = self.table.item(r, 5).text().strip() if self.table.item(r, 5) else ""
            if cat_col_hidden:
                product_category = ""
            else:
                w_cat = self.table.cellWidget(r, 6)
                product_category = w_cat.currentText() if w_cat is not None else ""
                # Bug 12 修复：每行产品类别做"宽容式"处理——无效值静默置空，
                # 不阻断整个批量流程（与共用业务员/客户的阻断式校验不同）。
                if (product_category
                        and w_cat is not None
                        and w_cat.findText(product_category) < 0):
                    product_category = ""
            chk_w = self.table.cellWidget(r, 7)
            chk = chk_w.findChild(QCheckBox) if chk_w else None
            needs_inspection = bool(chk and chk.isChecked())
            if not order_no:
                continue
            rows.append({
                "row_index": r,
                "order_type": order_type,
                "order_no": order_no,
                # 使用已校验过的 common_customer，避免再次调用 currentText() 拿到未校验值
                "customer": customer or common_customer,
                "product_info": product_info,
                "po_no": po_no,
                "product_category": product_category,
                "needs_inspection": needs_inspection and order_type == "外贸",
                # per-row 业务员优先（Excel 中填了业务员列），否则用页面顶部的共用业务员
                "salesperson": (per_row_sp or common_sales).strip(),
            })
        return rows

    def _set_status(self, row, text, color="#333"):
        it = QTableWidgetItem(text)
        it.setForeground(QBrush(QColor(color)))
        self.table.setItem(row, 8, it)

    # ============== 预览 & 执行 ==============
    def _preview_all(self):
        rows = self._collect_rows()
        if not rows:
            QMessageBox.information(self, "提示", "没有有效订单行")
            return
        for od in rows:
            try:
                base_path = self.storage.build_customer_dir(
                    od["salesperson"], od["customer"])
                if not base_path:
                    self._set_status(od["row_index"], "路径无效", "#E53935")
                    continue
                _, tpl = self.storage.match_template(od["salesperson"], od["customer"], od["order_type"])
                if not tpl:
                    self._set_status(od["row_index"], "无可用模板", "#E53935")
                    continue
                ctx = folder_builder.build_context(od)
                tpl_folders = folder_builder.flatten_template_folders(
                    tpl, base_path, ctx, od["needs_inspection"])
                tpl_folders, _ = folder_builder.compare_with_existing(
                    base_path, tpl_folders)
                exists = sum(1 for i in tpl_folders if i["status"] == "existing" and not i.get("is_root"))
                tocre = sum(1 for i in tpl_folders if i["status"] == "to_create" and not i.get("is_root"))
                root_existed = any(i["status"] == "existing" and i.get("is_root") for i in tpl_folders)
                if root_existed:
                    self._set_status(od["row_index"], f"待补建 {tocre}，已存在 {exists}", "#1976D2")
                else:
                    self._set_status(od["row_index"], f"待创建 {tocre} 个", "#1976D2")
            except Exception as e:
                self._set_status(od["row_index"], f"错误：{e}", "#E53935")

    def _run_all(self):
        rows = self._collect_rows()
        if not rows:
            QMessageBox.information(self, "提示", "没有有效订单行")
            return
        reply = QMessageBox.question(self, "确认",
                                     f"即将批量创建 {len(rows)} 笔订单文件夹，是否继续？")
        if reply != QMessageBox.Yes:
            return
        cfg = self.storage.load_config()
        tpl_dir = cfg.get("template_files_dir") or None
        success, fail = 0, 0
        details = []
        for od in rows:
            try:
                base_path = self.storage.build_customer_dir(
                    od["salesperson"], od["customer"])
                if not base_path:
                    self._set_status(od["row_index"], "路径无效", "#E53935")
                    fail += 1
                    continue
                tpl_name, tpl = self.storage.match_template(od["salesperson"], od["customer"], od["order_type"])
                if not tpl:
                    self._set_status(od["row_index"], "无可用模板", "#E53935")
                    fail += 1
                    continue
                result = folder_builder.execute_build(
                    order=od, template=tpl, base_path=base_path,
                    template_files_dir=tpl_dir,
                    origin_map=cfg.get("origin_map") or {},
                    origin_file_ext=cfg.get("origin_file_ext") or {})
                # 历史
                # 精简 copy_results：只保留关键字段，避免 history.json 过大
                slim_copy_results = []
                for cr in result["copy_results"]:
                    src = cr.get("src", "") or ""
                    dst = cr.get("dst", "") or ""
                    slim_copy_results.append({
                        "copied": bool(cr.get("copied")),
                        "src": os.path.basename(src) if src else "",
                        "dst": os.path.basename(dst) if dst else "",
                        "reason": cr.get("reason", ""),
                    })
                self.storage.append_history({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "operator": cfg.get("operator", ""),
                    "salesperson": od["salesperson"],
                    "customer": od["customer"],
                    "order_no": od["order_no"],
                    "order_type": od["order_type"],
                    "product_category": od["product_category"],
                    "template_name": tpl_name,
                    "path": result["base_path"],
                    "result": "成功",
                    "created_count": len(result["created"]),
                    "skipped_count": len(result["skipped"]),
                    "copied_count": sum(1 for r in result["copy_results"] if r.get("copied")),
                    # 新增：完整的创建结果详情，供历史记录「详情」按钮显示
                    "detail": {
                        "created": list(result["created"]),
                        "skipped": list(result["skipped"]),
                        "copy_results": slim_copy_results,
                        "checklist_path": result.get("checklist_path", ""),
                    },
                })
                self._set_status(od["row_index"],
                                 f"✅ 新建 {len(result['created'])}，跳过 {len(result['skipped'])}，复制模板 {sum(1 for r in result['copy_results'] if r.get('copied'))}",
                                 "#2E7D32")
                success += 1
                details.append(f"[{od['order_no']}] 新建 {len(result['created'])} / 跳过 {len(result['skipped'])} / 复制 {sum(1 for r in result['copy_results'] if r.get('copied'))}")
            except Exception as e:
                self._set_status(od["row_index"], f"❌ {e}", "#E53935")
                fail += 1
                details.append(f"[{od['order_no']}] 失败：{e}")

        # 汇总
        from PyQt5.QtWidgets import QDialog, QPlainTextEdit, QPushButton, QVBoxLayout
        dlg = QDialog(self)
        dlg.setWindowTitle("批量执行完成")
        dlg.resize(700, 460)
        v = QVBoxLayout(dlg)
        v.addWidget(QLabel(f"<b>成功 {success} 笔，失败 {fail} 笔。</b>"))
        tx = QPlainTextEdit()
        tx.setReadOnly(True)
        tx.setPlainText("\n".join(details))
        v.addWidget(tx)
        btn = QPushButton("关闭")
        btn.clicked.connect(dlg.accept)
        v.addWidget(btn)
        dlg.exec_()
