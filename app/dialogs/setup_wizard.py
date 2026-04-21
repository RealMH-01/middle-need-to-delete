# -*- coding: utf-8 -*-
"""首次启动向导 SetupWizard

面向首次使用程序的用户，用 4 步引导把程序跑起来：

1. 第一步：选择公司资料根目录
2. 第二步：确认订单文件夹 + 中间层设置
3. 第三步：产品类别 / 工厂映射（可跳过）
4. 第四步：导入业务员和客户（自动扫描）

视觉风格：Neo-brutalism —— 奶油色背景 + 纯黑粗边 + 直角 + 高饱和度按钮。
每一步内部都用 QScrollArea 包裹内容，底部导航条始终可见。

向导结束后通过 :meth:`collected_config` 返回一个完整的配置字典，
由 ``MainWindow`` 在创建 ``Storage`` 时一次性写入 config.json。
"""

from pathlib import Path
from typing import Any, Dict, List

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QFileDialog, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QRadioButton,
    QScrollArea, QSizePolicy, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QWidget,
)

from ..style import (
    COLOR_ACCENT, COLOR_BG, COLOR_INK, COLOR_MUTED, COLOR_SECONDARY,
    COLOR_WHITE,
)


# ------------------------------------------------------------------
# 样式片段（局部 QSS，覆盖少数全局样式）
# ------------------------------------------------------------------
_TIP_PURPLE_QSS = (
    f"QLabel {{"
    f"  background-color: {COLOR_MUTED};"
    f"  border: 4px solid {COLOR_INK};"
    f"  border-radius: 0px;"
    f"  padding: 10px 14px;"
    f"  color: {COLOR_INK};"
    f"  font-weight: bold;"
    f"}}"
)

_TIP_YELLOW_QSS = (
    f"QLabel {{"
    f"  background-color: {COLOR_SECONDARY};"
    f"  border: 4px solid {COLOR_INK};"
    f"  border-radius: 0px;"
    f"  padding: 12px 14px;"
    f"  color: {COLOR_INK};"
    f"  font-weight: bold;"
    f"}}"
)

_MONO_FAMILIES = ('"Consolas", "Courier New", "Monaco", "SF Mono", monospace')


def _is_hidden_name(name: str) -> bool:
    return name.startswith(".")


def _list_subfolders(path: Path) -> List[str]:
    """返回 path 下的一级子文件夹名（已按名称排序，排除隐藏目录）。"""
    try:
        if not path.exists() or not path.is_dir():
            return []
        return sorted(
            [p.name for p in path.iterdir()
             if p.is_dir() and not _is_hidden_name(p.name)]
        )
    except Exception:
        return []


# ==================================================================
# StepIndicator：顶部进度指示器
# ==================================================================
class StepIndicator(QWidget):
    """顶部步骤指示器：显示"第 N 步 / 共 4 步" + 4 个方块。"""

    def __init__(self, total: int = 4, parent=None):
        super().__init__(parent)
        self._total = total
        self._current = 0

        self._text = QLabel()
        self._text.setStyleSheet(
            f"color: {COLOR_INK}; font-weight: 900; font-size: 14px;"
        )

        self._dots_bar = QHBoxLayout()
        self._dots_bar.setSpacing(6)
        self._dots: List[QLabel] = []
        for _ in range(total):
            dot = QLabel()
            dot.setFixedSize(28, 14)
            self._dots.append(dot)
            self._dots_bar.addWidget(dot)
        self._dots_bar.addStretch(1)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        root.addWidget(self._text)
        root.addLayout(self._dots_bar, 1)

        self.set_current(0)

    def set_current(self, idx: int):
        self._current = max(0, min(idx, self._total - 1))
        self._text.setText(f"第 {self._current + 1} 步 / 共 {self._total} 步")
        for i, dot in enumerate(self._dots):
            if i <= self._current:
                bg = COLOR_ACCENT
            else:
                bg = COLOR_WHITE
            dot.setStyleSheet(
                f"QLabel {{"
                f"  background-color: {bg};"
                f"  border: 3px solid {COLOR_INK};"
                f"  border-radius: 0px;"
                f"}}"
            )


# ==================================================================
# SetupWizard 主类
# ==================================================================
class SetupWizard(QDialog):
    """首次启动向导对话框。

    向导结束后 ``exec_()`` 返回 ``QDialog.Accepted``，可通过
    :meth:`collected_config` 获取填写的数据。
    """

    TOTAL_STEPS = 4

    def __init__(self, parent=None):
        # 禁用关闭按钮：使用自定义关闭逻辑（closeEvent 拦截）
        flags = Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint
        super().__init__(parent, flags)

        self.setWindowTitle("首次设置向导")
        self.setModal(True)
        self.resize(800, 600)
        self.setMinimumSize(640, 480)

        # 收集的数据
        self._root_dir: str = ""
        self._order_root_folder: str = ""
        self._mid_keywords: List[str] = []
        self._origin_map: Dict[str, str] = {}
        self._origin_file_ext: Dict[str, str] = {}
        self._template_dir: str = ""
        self._scanned_rel_paths: List[str] = []

        # 第三步是否启用产品类别配置（用户点了"需要，我来配置"按钮）
        self._step3_enabled: bool = False

        self._build_ui()

    # ------------------------------------------------------------------
    # 对外 API
    # ------------------------------------------------------------------
    @property
    def root_dir(self) -> str:
        return self._root_dir

    def collected_config(self) -> Dict[str, Any]:
        return {
            "root_dir": self._root_dir,
            "order_root_folder": self._order_root_folder,
            "mid_layer_keywords": list(self._mid_keywords),
            "origin_map": dict(self._origin_map),
            "origin_file_ext": dict(self._origin_file_ext),
            "template_files_dir": self._template_dir,
            "scanned_salespersons": list(self._scanned_rel_paths),
        }

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        # ---- 顶部：步骤指示器 ----
        self.indicator = StepIndicator(self.TOTAL_STEPS)
        root.addWidget(self.indicator)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"background-color: {COLOR_INK}; min-height: 4px; max-height: 4px;"
            f"border: none;"
        )
        root.addWidget(sep)

        # ---- 中部：QStackedWidget ----
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_step0())
        self.stack.addWidget(self._build_step1())
        self.stack.addWidget(self._build_step2())
        self.stack.addWidget(self._build_step3())
        root.addWidget(self.stack, 1)

        # ---- 底部导航条 ----
        nav = QHBoxLayout()
        nav.setSpacing(12)

        self.btn_prev = QPushButton("上一步")
        self.btn_prev.setObjectName("SecondaryButton")
        self.btn_prev.clicked.connect(self._on_prev)

        nav.addWidget(self.btn_prev)
        nav.addStretch(1)

        self.btn_next = QPushButton("下一步  →")
        # 加大字号
        f = QFont()
        f.setBold(True)
        f.setPointSize(12)
        self.btn_next.setFont(f)
        self.btn_next.clicked.connect(self._on_next)
        nav.addWidget(self.btn_next)

        root.addLayout(nav)

        self._goto_step(0)

    # ------------------------------------------------------------------
    # 通用：把一个 content QWidget 包进 QScrollArea
    # ------------------------------------------------------------------
    def _wrap_scroll(self, content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(content)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        content.setStyleSheet(
            (content.styleSheet() or "") +
            f"\nQWidget#WizardStep {{ background: {COLOR_BG}; }}"
        )
        content.setObjectName("WizardStep")
        return scroll

    def _make_title(self, big: str, sub: str) -> QWidget:
        """生成每一步顶部的大标题 + 副标题。"""
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        title = QLabel(big)
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {COLOR_INK}; font-size: 24px; font-weight: 900;"
            f"background: transparent;"
        )
        lay.addWidget(title)

        subtitle = QLabel(sub)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"color: {COLOR_INK}; font-size: 16px; font-weight: bold;"
            f"background: transparent;"
        )
        lay.addWidget(subtitle)

        return box

    # ==================================================================
    # Step 0：选择根目录
    # ==================================================================
    def _build_step0(self) -> QWidget:
        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(16)

        v.addWidget(self._make_title(
            "欢迎使用订单文件夹工具 👋",
            "让我们花 2 分钟完成初始设置，之后就可以直接开始工作了。"
        ))

        # 说明
        desc = QLabel(
            "第一步：请选择你们公司存放所有业务资料的总文件夹。"
            "程序会在这个文件夹里面创建和管理订单目录。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {COLOR_INK}; font-size: 14px; font-weight: bold;"
            f"background: transparent;"
        )
        v.addWidget(desc)

        # 路径输入行
        row = QHBoxLayout()
        row.setSpacing(8)
        self.edit_root = QLineEdit()
        self.edit_root.setReadOnly(True)
        self.edit_root.setPlaceholderText("请点击右侧「浏览…」按钮选择一个文件夹")
        btn_browse = QPushButton("浏览…")
        btn_browse.setObjectName("SecondaryButton")
        btn_browse.clicked.connect(self._on_pick_root)
        row.addWidget(self.edit_root, 1)
        row.addWidget(btn_browse)
        v.addLayout(row)

        # 紫色提示
        tip = QLabel(
            "💡 举个例子：如果你们的资料都放在 D:\\公司资料 下面，就选这个文件夹。"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet(_TIP_PURPLE_QSS)
        v.addWidget(tip)

        # 目录结构示意
        tree_lbl = QLabel(
            "你选择的根目录/\n"
            "├── 订单文件夹/        ← 程序会在这里创建订单\n"
            "│   ├── 张三/\n"
            "│   ├── 李四/\n"
            "│   └── ...\n"
            "├── 模板文件/          ← 可选，存放空白模板\n"
            "└── 其他文件夹/        ← 程序不会碰这些"
        )
        tree_lbl.setStyleSheet(
            f"QLabel {{"
            f"  background-color: {COLOR_WHITE};"
            f"  border: 4px solid {COLOR_INK};"
            f"  border-radius: 0px;"
            f"  padding: 12px 16px;"
            f"  color: {COLOR_INK};"
            f"  font-family: {_MONO_FAMILIES};"
            f"  font-size: 13px;"
            f"  font-weight: bold;"
            f"}}"
        )
        tree_lbl.setTextFormat(Qt.PlainText)
        v.addWidget(tree_lbl)

        v.addStretch(1)
        return self._wrap_scroll(content)

    def _on_pick_root(self):
        d = QFileDialog.getExistingDirectory(
            self, "选择公司资料根目录", self._root_dir or str(Path.home())
        )
        if d:
            self._root_dir = d
            self.edit_root.setText(d)
            self._update_next_enabled()

    # ==================================================================
    # Step 1：确认订单文件夹 + 中间层
    # ==================================================================
    def _build_step1(self) -> QWidget:
        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(16)

        v.addWidget(self._make_title(
            "第二步：哪个文件夹是用来存放订单的？",
            "程序会在这个文件夹里按「业务员 → 客户 → 订单号」的结构创建目录。"
        ))

        # --- 文件夹列表 ---
        list_lbl = QLabel("下面是你刚才选的根目录里的文件夹，请选一个用来存放订单：")
        list_lbl.setWordWrap(True)
        list_lbl.setStyleSheet(
            f"color: {COLOR_INK}; font-weight: bold; background: transparent;"
        )
        v.addWidget(list_lbl)

        self.list_order = QListWidget()
        self.list_order.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_order.setMinimumHeight(140)
        self.list_order.itemSelectionChanged.connect(self._update_next_enabled)
        v.addWidget(self.list_order)

        # "自己输入"
        self.chk_custom_order = QCheckBox("以上都不是，我想自己输入文件夹名")
        self.chk_custom_order.stateChanged.connect(self._on_toggle_custom_order)
        v.addWidget(self.chk_custom_order)

        cust_row = QHBoxLayout()
        cust_row.setSpacing(8)
        self.edit_custom_order = QLineEdit()
        self.edit_custom_order.setPlaceholderText(
            "请输入文件夹名，如 Orders、订单管理"
        )
        self.edit_custom_order.textChanged.connect(
            self._on_custom_order_text_changed)
        self.lbl_will_create = QLabel("")
        self.lbl_will_create.setStyleSheet(
            f"color: {COLOR_INK}; font-weight: bold; background: transparent;"
        )
        cust_row.addWidget(self.edit_custom_order, 1)
        cust_row.addWidget(self.lbl_will_create)
        self._custom_order_container = QWidget()
        self._custom_order_container.setLayout(cust_row)
        self._custom_order_container.setVisible(False)
        v.addWidget(self._custom_order_container)

        # --- 分隔 ---
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"background-color: {COLOR_INK}; min-height: 4px; max-height: 4px;"
            f"border: none; margin: 10px 0;"
        )
        v.addWidget(sep)

        # --- 中间层 ---
        mid_lbl = QLabel(
            "你们的业务员文件夹下面，是否还有一层叫「进行中订单」之类的子文件夹？"
        )
        mid_lbl.setWordWrap(True)
        mid_lbl.setStyleSheet(
            f"color: {COLOR_INK}; font-size: 15px; font-weight: 900;"
            f"background: transparent;"
        )
        v.addWidget(mid_lbl)

        self.rb_no_mid = QRadioButton("否，业务员文件夹下面直接就是客户文件夹")
        self.rb_yes_mid = QRadioButton("是，中间还有一层")
        self.rb_no_mid.setChecked(True)
        self.rb_no_mid.toggled.connect(self._on_mid_toggle)
        v.addWidget(self.rb_no_mid)
        v.addWidget(self.rb_yes_mid)

        self.edit_mid_kw = QLineEdit()
        self.edit_mid_kw.setPlaceholderText(
            "请输入关键词，用逗号分隔，如：进行, 订单"
        )
        self.edit_mid_kw.setText("进行, 订单")
        self.edit_mid_kw.setVisible(False)
        v.addWidget(self.edit_mid_kw)

        v.addStretch(1)
        return self._wrap_scroll(content)

    def _populate_step1_list(self):
        """进入第二步时填充文件夹列表。"""
        self.list_order.clear()
        if not self._root_dir:
            return
        names = _list_subfolders(Path(self._root_dir))
        default_idx = -1
        for i, name in enumerate(names):
            it = QListWidgetItem(f"📁  {name}")
            it.setData(Qt.UserRole, name)
            self.list_order.addItem(it)
            if name == "1订单":
                default_idx = i
        if default_idx >= 0:
            self.list_order.setCurrentRow(default_idx)
        elif self.list_order.count() > 0:
            # 不默认选中，让用户自己挑
            pass

    def _on_toggle_custom_order(self, _state):
        use_custom = self.chk_custom_order.isChecked()
        self.list_order.setEnabled(not use_custom)
        self._custom_order_container.setVisible(use_custom)
        if use_custom:
            self.edit_custom_order.setFocus()
            self._on_custom_order_text_changed(self.edit_custom_order.text())
        else:
            self.lbl_will_create.setText("")
        self._update_next_enabled()

    def _on_custom_order_text_changed(self, text: str):
        text = (text or "").strip()
        if text and self._root_dir:
            folder = Path(self._root_dir) / text
            if folder.exists() and folder.is_dir():
                self.lbl_will_create.setText("（已存在 ✓）")
            else:
                self.lbl_will_create.setText("（将自动创建）")
        else:
            self.lbl_will_create.setText("")
        self._update_next_enabled()

    def _on_mid_toggle(self):
        self.edit_mid_kw.setVisible(self.rb_yes_mid.isChecked())

    def _collect_step1(self) -> bool:
        """收集第二步数据到 self。返回是否有效。"""
        if self.chk_custom_order.isChecked():
            name = (self.edit_custom_order.text() or "").strip()
            if not name:
                QMessageBox.warning(
                    self, "提示", "请输入订单文件夹名，或取消勾选改从列表选择。"
                )
                return False
            # 基础字符校验
            bad = set('<>:"/\\|?*')
            for ch in name:
                if ch in bad:
                    QMessageBox.warning(
                        self, "格式错误",
                        f"文件夹名中不能包含字符：{ch}\n"
                        f"不允许的字符：<>:\"/\\|?*"
                    )
                    return False
            self._order_root_folder = name
        else:
            cur = self.list_order.currentItem()
            if not cur:
                QMessageBox.warning(
                    self, "提示",
                    "请从列表中选择一个文件夹，或勾选「以上都不是」自己输入。"
                )
                return False
            self._order_root_folder = cur.data(Qt.UserRole)

        # 中间层
        if self.rb_yes_mid.isChecked():
            raw = (self.edit_mid_kw.text() or "").strip()
            kws: List[str] = []
            seen = set()
            for part in raw.replace("，", ",").split(","):
                p = part.strip()
                if p and p not in seen:
                    kws.append(p)
                    seen.add(p)
            if not kws:
                QMessageBox.warning(
                    self, "提示",
                    "请输入至少一个中间层关键词，或选择「否」。"
                )
                return False
            self._mid_keywords = kws
        else:
            self._mid_keywords = []

        return True

    # ==================================================================
    # Step 2：产品类别配置
    # ==================================================================
    def _build_step2(self) -> QWidget:
        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(16)

        v.addWidget(self._make_title(
            "第三步：你们的产品需要由不同的工厂生产吗？",
            "有些公司的不同产品会分配到不同的工厂或分公司生产，"
            "程序可以根据产品类别自动选择对应的模板文件。"
            "如果你们公司没有这种情况，直接跳过就好。"
        ))

        # 两个大按钮
        big_row = QHBoxLayout()
        big_row.setSpacing(14)
        self.btn_skip_step2 = QPushButton("不需要，跳过这一步  →")
        self.btn_skip_step2.setObjectName("SecondaryButton")
        self.btn_skip_step2.setMinimumHeight(80)
        self.btn_skip_step2.clicked.connect(self._on_step2_skip)

        self.btn_need_step2 = QPushButton("需要，我来配置")
        # 不设 objectName，默认就是热红主按钮
        self.btn_need_step2.setMinimumHeight(80)
        self.btn_need_step2.clicked.connect(self._on_step2_configure)

        big_row.addWidget(self.btn_skip_step2, 1)
        big_row.addWidget(self.btn_need_step2, 1)
        v.addLayout(big_row)

        # 配置区域（默认隐藏）
        self._step2_config = QWidget()
        cfg_lay = QVBoxLayout(self._step2_config)
        cfg_lay.setContentsMargins(0, 0, 0, 0)
        cfg_lay.setSpacing(10)

        cfg_tip = QLabel(
            "请填写你们公司的产品类别，以及它们各自对应的工厂/产地名称。"
            "填完后程序会自动为每个工厂生成基础的模板映射，以后可随时修改。"
        )
        cfg_tip.setWordWrap(True)
        cfg_tip.setStyleSheet(
            f"color: {COLOR_INK}; font-weight: bold; background: transparent;"
        )
        cfg_lay.addWidget(cfg_tip)

        # 表格
        self.tbl_origin = QTableWidget(0, 2)
        self.tbl_origin.setHorizontalHeaderLabels(
            ["产品类别名称", "对应工厂/产地名称"])
        self.tbl_origin.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.tbl_origin.verticalHeader().setVisible(False)
        self.tbl_origin.setMinimumHeight(140)
        self.tbl_origin.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_origin.insertRow(0)
        self.tbl_origin.setItem(0, 0, QTableWidgetItem(""))
        self.tbl_origin.setItem(0, 1, QTableWidgetItem(""))
        cfg_lay.addWidget(self.tbl_origin)

        # +/- 按钮
        tbl_btns = QHBoxLayout()
        btn_add = QPushButton("+ 新增")
        btn_add.setObjectName("SecondaryButton")
        btn_add.clicked.connect(self._on_origin_add)
        btn_del = QPushButton("- 删除选中")
        btn_del.setObjectName("SecondaryButton")
        btn_del.clicked.connect(self._on_origin_del)
        tbl_btns.addWidget(btn_add)
        tbl_btns.addWidget(btn_del)
        tbl_btns.addStretch(1)
        cfg_lay.addLayout(tbl_btns)

        # 分隔
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"background-color: {COLOR_INK}; min-height: 4px; max-height: 4px;"
            f"border: none; margin: 8px 0;"
        )
        cfg_lay.addWidget(sep)

        # 模板文件目录
        tpl_lbl = QLabel("模板文件目录（可选）：")
        tpl_lbl.setStyleSheet(
            f"color: {COLOR_INK}; font-size: 15px; font-weight: 900;"
            f"background: transparent;"
        )
        cfg_lay.addWidget(tpl_lbl)

        tpl_row = QHBoxLayout()
        tpl_row.setSpacing(8)
        self.edit_tpl_dir = QLineEdit()
        self.edit_tpl_dir.setReadOnly(True)
        self.edit_tpl_dir.setPlaceholderText("（未设置）")
        btn_tpl = QPushButton("浏览…")
        btn_tpl.setObjectName("SecondaryButton")
        btn_tpl.clicked.connect(self._on_pick_tpl_dir)
        tpl_row.addWidget(self.edit_tpl_dir, 1)
        tpl_row.addWidget(btn_tpl)
        cfg_lay.addLayout(tpl_row)

        tpl_tip = QLabel(
            "💡 如果你有预先准备好的空白模板文件（如合同模板、发票模板），"
            "可以选择存放它们的文件夹。没有的话可以跳过，以后随时在首页设置。"
        )
        tpl_tip.setWordWrap(True)
        tpl_tip.setStyleSheet(_TIP_PURPLE_QSS)
        cfg_lay.addWidget(tpl_tip)

        self._step2_config.setVisible(False)
        v.addWidget(self._step2_config)

        v.addStretch(1)
        return self._wrap_scroll(content)

    def _on_step2_skip(self):
        """点了"跳过"——直接前进到第四步。"""
        self._step3_enabled = False
        self._origin_map = {}
        self._origin_file_ext = {}
        self._template_dir = ""
        # 进入第四步前，需要先根据前面的选择扫描一下
        if not self._prepare_step3():
            return
        self._goto_step(3)

    def _on_step2_configure(self):
        """点了"需要"——展开配置区域并滚动到可见。"""
        self._step3_enabled = True
        self._step2_config.setVisible(True)
        # 把"配置"按钮改成"已展开"样式提示
        self.btn_need_step2.setEnabled(False)
        self.btn_skip_step2.setEnabled(False)
        # 展开后立刻滚动到配置区域，避免它出现在视口外用户看不到。
        # 用 QTimer.singleShot(0) 延迟到下一次事件循环执行，确保
        # setVisible(True) 引发的布局重算已经完成，
        # ensureWidgetVisible 才能拿到正确的 widget 坐标。
        QTimer.singleShot(0, self._scroll_step2_to_config)

    def _scroll_step2_to_config(self):
        """让 Step 2 的配置区域滚入视口。"""
        # Step 2 是 stack 的第 3 个 widget（index=2），它是 _wrap_scroll
        # 返回的 QScrollArea。我们让配置区域带 50 px 边距进入视口。
        try:
            scroll_area = self.stack.widget(2)
        except Exception:
            return
        if scroll_area is not None and hasattr(scroll_area, "ensureWidgetVisible"):
            scroll_area.ensureWidgetVisible(self._step2_config, 50, 50)

    def _on_origin_add(self):
        r = self.tbl_origin.rowCount()
        self.tbl_origin.insertRow(r)
        self.tbl_origin.setItem(r, 0, QTableWidgetItem(""))
        self.tbl_origin.setItem(r, 1, QTableWidgetItem(""))

    def _on_origin_del(self):
        rows = sorted(
            {i.row() for i in self.tbl_origin.selectedIndexes()},
            reverse=True
        )
        for r in rows:
            self.tbl_origin.removeRow(r)
        if self.tbl_origin.rowCount() == 0:
            self._on_origin_add()

    def _on_pick_tpl_dir(self):
        start = self._template_dir or self._root_dir or str(Path.home())
        d = QFileDialog.getExistingDirectory(
            self, "选择模板文件目录", start
        )
        if d:
            self._template_dir = d
            self.edit_tpl_dir.setText(d)

    def _collect_step2(self) -> bool:
        """用户走到本步并点"下一步"或"完成"时收集数据。"""
        if not self._step3_enabled:
            # 已经通过 _on_step2_skip 处理，不会走到这里
            return True

        origin_map: Dict[str, str] = {}
        for r in range(self.tbl_origin.rowCount()):
            k_item = self.tbl_origin.item(r, 0)
            v_item = self.tbl_origin.item(r, 1)
            k = (k_item.text() if k_item else "").strip()
            v = (v_item.text() if v_item else "").strip()
            if k and v:
                origin_map[k] = v
            elif k or v:
                QMessageBox.warning(
                    self, "提示",
                    f"第 {r + 1} 行的产品类别或工厂名没填完整，请补完或删除这一行。"
                )
                return False

        self._origin_map = origin_map

        # 根据工厂名自动生成 origin_file_ext
        ext_map: Dict[str, str] = {}
        for factory in set(origin_map.values()):
            if not factory:
                continue
            ext_map[f"{factory}/外贸生产"] = ".doc"
            ext_map[f"{factory}/外贸发货"] = ".docx"
            ext_map[f"{factory}/内贸生产"] = ".xlsx"
            ext_map[f"{factory}/内贸发货"] = ".xlsx"
        self._origin_file_ext = ext_map

        return True

    # ==================================================================
    # Step 3：导入业务员
    # ==================================================================
    def _build_step3(self) -> QWidget:
        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(16)

        v.addWidget(self._make_title(
            "最后一步：导入业务员和客户 🎉",
            "程序已经自动扫描了你的订单文件夹，"
            "请勾选哪些是业务员的文件夹。"
        ))

        # 主体容器（扫描结果 vs 空状态二选一）
        self._step3_body = QWidget()
        self._step3_body_layout = QVBoxLayout(self._step3_body)
        self._step3_body_layout.setContentsMargins(0, 0, 0, 0)
        self._step3_body_layout.setSpacing(10)
        v.addWidget(self._step3_body, 1)

        # 树控件（之后按扫描结果填充）
        self.tree_sp = QTreeWidget()
        self.tree_sp.setHeaderHidden(True)
        self.tree_sp.setMinimumHeight(220)

        # 空状态提示
        self.lbl_empty = QLabel(
            "📂 订单文件夹里还没有任何子文件夹，这很正常——"
            "可能你还没有开始使用。没关系，你可以之后在程序首页手动添加"
            "业务员和客户，或者往订单文件夹里建好业务员文件夹后再点"
            "「扫描导入」。"
        )
        self.lbl_empty.setWordWrap(True)
        self.lbl_empty.setStyleSheet(_TIP_YELLOW_QSS)

        # 底部小提示
        self.lbl_pick_tip = QLabel(
            "✅ 勾选的文件夹会被导入为业务员，它们下面的子文件夹会被导入为客户。"
            "不确定的可以先全部勾选，以后再调整。"
        )
        self.lbl_pick_tip.setWordWrap(True)
        self.lbl_pick_tip.setStyleSheet(
            f"color: {COLOR_INK}; font-weight: bold; background: transparent;"
        )

        # 先占位，_prepare_step3 会动态填充
        return self._wrap_scroll(content)

    def _prepare_step3(self) -> bool:
        """进入第四步前扫描订单文件夹并填充树。返回是否成功。"""
        # 清理 body
        while self._step3_body_layout.count():
            item = self._step3_body_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

        if not self._root_dir or not self._order_root_folder:
            QMessageBox.warning(
                self, "提示",
                "请先完成前面的步骤（根目录 + 订单文件夹名）。"
            )
            return False

        order_root = Path(self._root_dir) / self._order_root_folder
        # 如果自己输入了一个不存在的文件夹，提示要不要创建
        if not order_root.exists():
            try:
                order_root.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self, "创建失败",
                    f"无法在根目录下创建文件夹「{self._order_root_folder}」：{e}"
                )
                return False

        first_level = _list_subfolders(order_root)

        if not first_level:
            # 空状态
            self._step3_body_layout.addWidget(self.lbl_empty)
            return True

        # 填充树
        self.tree_sp.clear()
        for name in first_level:
            path1 = order_root / name
            subs = _list_subfolders(path1)
            n = len(subs)
            node = QTreeWidgetItem(self.tree_sp)
            node.setText(0, f"📁 {name}    （{n} 个子文件夹）")
            node.setData(0, Qt.UserRole, name)  # rel_path
            node.setFlags(node.flags() | Qt.ItemIsUserCheckable)
            node.setCheckState(0, Qt.Checked)
            # 展开二级
            for sub in subs:
                path2 = path1 / sub
                sub_subs = _list_subfolders(path2)
                m = len(sub_subs)
                child = QTreeWidgetItem(node)
                child.setText(0, f"📁 {sub}    （{m} 个子文件夹）")
                child.setData(0, Qt.UserRole, f"{name}/{sub}")
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)
            node.setExpanded(True)

        self._step3_body_layout.addWidget(self.tree_sp)
        self._step3_body_layout.addWidget(self.lbl_pick_tip)
        return True

    def _collect_step3(self) -> bool:
        """收集勾选的业务员相对路径。"""
        paths: List[str] = []
        # 遍历树
        root = self.tree_sp.invisibleRootItem()
        for i in range(root.childCount()):
            node = root.child(i)
            if node.checkState(0) == Qt.Checked:
                rel = node.data(0, Qt.UserRole)
                if rel:
                    paths.append(rel)
            # 二级：如果单独勾了二级
            for j in range(node.childCount()):
                child = node.child(j)
                if child.checkState(0) == Qt.Checked:
                    rel = child.data(0, Qt.UserRole)
                    if rel:
                        paths.append(rel)
        # 去重
        seen = set()
        uniq: List[str] = []
        for p in paths:
            if p not in seen:
                uniq.append(p)
                seen.add(p)
        self._scanned_rel_paths = uniq
        return True

    # ==================================================================
    # 导航
    # ==================================================================
    def _goto_step(self, idx: int):
        idx = max(0, min(idx, self.TOTAL_STEPS - 1))
        self.stack.setCurrentIndex(idx)
        self.indicator.set_current(idx)
        self.btn_prev.setVisible(idx > 0)

        if idx == self.TOTAL_STEPS - 1:
            self.btn_next.setText("完成设置  ✓")
        else:
            self.btn_next.setText("下一步  →")

        # 进入各步时的初始化
        if idx == 1:
            self._populate_step1_list()
        # 第 4 步的初始化在 _prepare_step3 中，由调用方触发

        self._update_next_enabled()

    def _update_next_enabled(self):
        idx = self.stack.currentIndex()
        ok = True
        if idx == 0:
            ok = bool(self._root_dir) and Path(self._root_dir).is_dir()
        elif idx == 1:
            if self.chk_custom_order.isChecked():
                ok = bool((self.edit_custom_order.text() or "").strip())
            else:
                ok = self.list_order.currentItem() is not None
        # 第 2、3 步恒 True
        self.btn_next.setEnabled(ok)

    def _on_prev(self):
        idx = self.stack.currentIndex()
        if idx <= 0:
            return
        # 从第三步返回第二步时，把"跳过/配置"按钮恢复可点
        if idx == 3:
            self.btn_need_step2.setEnabled(True)
            self.btn_skip_step2.setEnabled(True)
        self._goto_step(idx - 1)

    def _on_next(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            if not self._root_dir:
                return
            self._goto_step(1)
            return
        if idx == 1:
            if not self._collect_step1():
                return
            self._goto_step(2)
            return
        if idx == 2:
            # 如果用户点了配置按钮，继续收集；否则（按了跳过）不会走到这里
            if self._step3_enabled:
                if not self._collect_step2():
                    return
            if not self._prepare_step3():
                return
            self._goto_step(3)
            return
        if idx == 3:
            # 完成
            if not self._collect_step3():
                return
            self.accept()
            return

    # ------------------------------------------------------------------
    # 关闭确认（替代窗口关闭按钮的行为；本向导已隐藏关闭按钮，
    # 但为了防止 Esc 键或其它路径的关闭，仍拦截一下）
    # ------------------------------------------------------------------
    def reject(self):  # noqa: D401
        """阻止通过 Esc 等途径直接关闭向导。"""
        ret = QMessageBox.question(
            self, "确认退出",
            "确定要退出吗？退出后下次打开程序还会再次弹出向导。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            super().reject()

    def closeEvent(self, event):  # noqa: N802
        # 基本上不会被触发（关闭按钮已去除），但以防万一
        ret = QMessageBox.question(
            self, "确认退出",
            "确定要退出吗？退出后下次打开程序还会再次弹出向导。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            event.accept()
            super().reject()
        else:
            event.ignore()
