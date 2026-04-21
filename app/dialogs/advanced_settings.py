# -*- coding: utf-8 -*-
"""高级设置对话框。

允许用户在不改代码的情况下调整"通用化改造"相关的配置项：
1. 订单根文件夹名（order_root_folder）
2. 中间层关键词（mid_layer_keywords）
3. 产品类别 → 产地 映射（origin_map）
4. 产地/文档类型 → 扩展名映射（origin_file_ext）

这些配置保存在 <根目录>/.order_tool/config.json 中。
对话框以 QTableWidget + QLineEdit 的形式呈现，便于非技术用户编辑。
"""

import re
from typing import Any, Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QFrame, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QScrollArea, QSpacerItem, QSizePolicy, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..style import COLOR_INK, COLOR_MUTED


# 同时支持中英文逗号分隔
_COMMA_SPLIT_RE = re.compile(r"[,，]")


class AdvancedSettingsDialog(QDialog):
    """高级设置对话框。"""

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle("⚙ 高级设置")
        self.resize(720, 640)
        self.setMinimumSize(500, 400)
        self.setModal(True)

        self._build_ui()
        self._load_from_config()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        # 顶部说明（固定在顶部，不随内容滚动）
        intro = QLabel(
            "在这里可以调整程序的通用化配置。大多数情况下保持默认即可。"
            "<br/>修改后点「保存」会立即生效。"
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(
            f"QLabel {{"
            f"  background-color: {COLOR_MUTED};"
            f"  border: 4px solid {COLOR_INK};"
            f"  border-radius: 0px;"
            f"  padding: 10px 14px;"
            f"  color: {COLOR_INK};"
            f"  font-weight: bold;"
            f"}}"
        )
        root.addWidget(intro)

        # ---- 中部：QScrollArea 承载四个 GroupBox ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # ---- 区域一：订单根文件夹名 ----
        grp1 = QGroupBox("① 订单根文件夹名")
        g1_layout = QVBoxLayout(grp1)
        g1_tip = QLabel(
            "订单所在的一级文件夹名称（如 1订单、Orders、订单管理）"
        )
        g1_tip.setStyleSheet("color:#000000;font-size:12px;")
        g1_layout.addWidget(g1_tip)
        self.edit_order_root = QLineEdit()
        self.edit_order_root.setPlaceholderText("例如 1订单 / Orders / 订单管理")
        g1_layout.addWidget(self.edit_order_root)
        content_layout.addWidget(grp1)

        # ---- 区域二：中间层关键词 ----
        grp2 = QGroupBox("② 中间层关键词")
        g2_layout = QVBoxLayout(grp2)
        g2_tip = QLabel(
            "文件夹名同时包含这些关键词时，会被识别为中间层"
            "（留空则不启用中间层识别）。用中文或英文逗号分隔。"
        )
        g2_tip.setWordWrap(True)
        g2_tip.setStyleSheet("color:#000000;font-size:12px;")
        g2_layout.addWidget(g2_tip)
        self.edit_mid_kws = QLineEdit()
        self.edit_mid_kws.setPlaceholderText("例如：进行, 订单")
        g2_layout.addWidget(self.edit_mid_kws)
        content_layout.addWidget(grp2)

        # ---- 区域三：产品类别与产地映射 ----
        grp3 = QGroupBox("③ 产品类别与产地映射")
        g3_layout = QVBoxLayout(grp3)
        g3_tip = QLabel(
            "每个产品类别对应一个产地（工厂）名称。创建订单时程序会按"
            "当前选择的「产品类别」查找产地，再用产地定位模板文件。"
        )
        g3_tip.setWordWrap(True)
        g3_tip.setStyleSheet("color:#000000;font-size:12px;")
        g3_layout.addWidget(g3_tip)

        self.tbl_origin_map = QTableWidget(0, 2)
        self.tbl_origin_map.setHorizontalHeaderLabels(["产品类别", "对应产地（工厂名）"])
        self.tbl_origin_map.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.tbl_origin_map.verticalHeader().setVisible(False)
        self.tbl_origin_map.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_origin_map.setMinimumHeight(120)
        g3_layout.addWidget(self.tbl_origin_map)

        g3_btns = QHBoxLayout()
        btn_om_add = QPushButton("+ 新增")
        btn_om_add.setObjectName("SecondaryButton")
        btn_om_add.clicked.connect(
            lambda: self._add_row(self.tbl_origin_map, "", ""))
        btn_om_del = QPushButton("- 删除选中")
        btn_om_del.setObjectName("SecondaryButton")
        btn_om_del.clicked.connect(
            lambda: self._del_selected_rows(self.tbl_origin_map))
        g3_btns.addWidget(btn_om_add)
        g3_btns.addWidget(btn_om_del)
        g3_btns.addStretch(1)
        g3_layout.addLayout(g3_btns)
        content_layout.addWidget(grp3)

        # ---- 区域四：产地文件扩展名映射 ----
        grp4 = QGroupBox("④ 产地文件扩展名映射")
        g4_layout = QVBoxLayout(grp4)
        g4_tip = QLabel(
            "形如「产地/文档类型」的组合对应的模板文件扩展名（如"
            " <code>.doc</code> / <code>.xlsx</code>）。一般不用改。"
        )
        g4_tip.setWordWrap(True)
        g4_tip.setStyleSheet("color:#000000;font-size:12px;")
        g4_layout.addWidget(g4_tip)

        self.tbl_ext_map = QTableWidget(0, 2)
        self.tbl_ext_map.setHorizontalHeaderLabels(
            ["产地/文档类型（如 华北工厂/外贸生产）", "扩展名（如 .doc）"])
        self.tbl_ext_map.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.tbl_ext_map.verticalHeader().setVisible(False)
        self.tbl_ext_map.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_ext_map.setMinimumHeight(140)
        g4_layout.addWidget(self.tbl_ext_map)

        g4_btns = QHBoxLayout()
        btn_ext_add = QPushButton("+ 新增")
        btn_ext_add.setObjectName("SecondaryButton")
        btn_ext_add.clicked.connect(
            lambda: self._add_row(self.tbl_ext_map, "", ""))
        btn_ext_del = QPushButton("- 删除选中")
        btn_ext_del.setObjectName("SecondaryButton")
        btn_ext_del.clicked.connect(
            lambda: self._del_selected_rows(self.tbl_ext_map))
        g4_btns.addWidget(btn_ext_add)
        g4_btns.addWidget(btn_ext_del)
        g4_btns.addStretch(1)
        g4_layout.addLayout(g4_btns)
        content_layout.addWidget(grp4)

        # 弹性空白：让内容少时不把 GroupBox 拉变形
        content_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        scroll.setWidget(content)
        root.addWidget(scroll, 1)  # 占满中部，可滚动

        # ---- 底部按钮（固定在底部，不滚动）----
        btns = QDialogButtonBox()
        self.btn_save = btns.addButton("保存", QDialogButtonBox.AcceptRole)
        # Neo-brutalism 主按钮（默认就是热红），保持默认 objectName 即可
        self.btn_cancel = btns.addButton("取消", QDialogButtonBox.RejectRole)
        self.btn_cancel.setObjectName("SecondaryButton")
        # 重新 polish 一下，让 QSS 按 objectName 生效
        self.btn_cancel.style().unpolish(self.btn_cancel)
        self.btn_cancel.style().polish(self.btn_cancel)
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    # ------------------------------------------------------------------
    # 数据加载 / 保存
    # ------------------------------------------------------------------
    def _load_from_config(self):
        """从 config.json 读取并填入各控件。"""
        cfg = self.storage.load_config() if self.storage else {}

        # 订单根文件夹名
        self.edit_order_root.setText(cfg.get("order_root_folder", "1订单") or "")

        # 中间层关键词
        kws = cfg.get("mid_layer_keywords", []) or []
        self.edit_mid_kws.setText(", ".join(kws))

        # 产品类别 → 产地
        origin_map = cfg.get("origin_map", {}) or {}
        self.tbl_origin_map.setRowCount(0)
        for k, v in origin_map.items():
            self._add_row(self.tbl_origin_map, str(k), str(v))

        # 产地/文档类型 → 扩展名
        ext_map = cfg.get("origin_file_ext", {}) or {}
        self.tbl_ext_map.setRowCount(0)
        for k, v in ext_map.items():
            self._add_row(self.tbl_ext_map, str(k), str(v))

    def _collect(self) -> Dict[str, Any]:
        """从控件收集数据，返回待写入 config 的 dict。"""
        order_root = (self.edit_order_root.text() or "").strip()
        if not order_root:
            order_root = "1订单"

        # 中间层关键词：支持中英文逗号分隔，过滤空项与重复项
        raw = self.edit_mid_kws.text() or ""
        kws: List[str] = []
        seen = set()
        for part in _COMMA_SPLIT_RE.split(raw):
            p = part.strip()
            if p and p not in seen:
                kws.append(p)
                seen.add(p)

        origin_map = self._collect_table_as_dict(self.tbl_origin_map)
        origin_file_ext = self._collect_table_as_dict(self.tbl_ext_map)

        return {
            "order_root_folder": order_root,
            "mid_layer_keywords": kws,
            "origin_map": origin_map,
            "origin_file_ext": origin_file_ext,
        }

    def _on_save(self):
        data = self._collect()
        if not self.storage:
            QMessageBox.warning(self, "提示", "未连接到存储，无法保存。")
            return
        # 基础校验：订单根文件夹名不得包含非法字符
        bad = set('<>:"/\\|?*')
        for ch in data["order_root_folder"]:
            if ch in bad:
                QMessageBox.warning(
                    self, "格式错误",
                    f'订单根文件夹名中不能包含字符：{ch}\n'
                    f'不允许的字符：<>:"/\\|?*'
                )
                return
        try:
            cfg = self.storage.load_config()
            cfg.update(data)
            self.storage.save_config(cfg)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"写入 config.json 失败：{e}")
            return
        self.accept()

    # ------------------------------------------------------------------
    # 表格工具
    # ------------------------------------------------------------------
    def _add_row(self, table: QTableWidget, k: str = "", v: str = ""):
        r = table.rowCount()
        table.insertRow(r)
        table.setItem(r, 0, QTableWidgetItem(k))
        table.setItem(r, 1, QTableWidgetItem(v))

    def _del_selected_rows(self, table: QTableWidget):
        rows = sorted({i.row() for i in table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        for r in rows:
            table.removeRow(r)

    def _collect_table_as_dict(self, table: QTableWidget) -> Dict[str, str]:
        """收集表格两列 → dict。空 key 跳过，后出现的 key 会覆盖之前的。"""
        out: Dict[str, str] = {}
        for r in range(table.rowCount()):
            k_item = table.item(r, 0)
            v_item = table.item(r, 1)
            k = (k_item.text() if k_item else "").strip()
            v = (v_item.text() if v_item else "").strip()
            if not k:
                continue
            out[k] = v
        return out
