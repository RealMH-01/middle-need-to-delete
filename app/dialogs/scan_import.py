# -*- coding: utf-8 -*-
"""
扫描导入业务员对话框。

用户点击首页「扫描导入业务员」按钮后：
1. 程序在 <根目录>/<订单根文件夹>/ 下列出所有第一层文件夹
2. 以树形勾选列表展示，每个文件夹旁边有复选框 + 层级标注下拉框
3. 层级标注下拉框让用户显式告诉程序这个文件夹是什么角色：
     - 第 1 层："业务员" / "分公司/区域（展开看子级）" / "忽略"
     - 第 2 层（分公司的子）："业务员" / "忽略"
   程序会根据文件夹下是否有子文件夹自动设置默认标注，
   勾选/取消行为也会与标注联动，多数情况下用户不需要手动改。
4. 用户点"确认导入"，对话框返回被选中项的列表：
      [{"name": "张三", "rel_path": "张三"},
       {"name": "赵六", "rel_path": "华南分公司/赵六"}, ...]
   调用方再调用 Storage.import_scanned_salespersons(rel_paths) 完成导入。
"""

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout
)


# 层级标注选项常量
LABEL_SALESPERSON = "业务员"
LABEL_BRANCH = "分公司/区域（展开看子级）"
LABEL_IGNORE = "忽略"

LEVEL1_OPTIONS = [LABEL_SALESPERSON, LABEL_BRANCH, LABEL_IGNORE]
LEVEL2_OPTIONS = [LABEL_SALESPERSON, LABEL_IGNORE]

# Qt UserRole 附加数据键
_ROLE_INFO = Qt.UserRole       # {"rel_path": ..., "abs": ..., "level": 1|2}


class ScanImportDialog(QDialog):
    """扫描导入业务员对话框"""

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle("扫描导入业务员")
        self.resize(820, 660)
        self._order_root = ""
        self._selected_rel_paths = []  # 确认后的结果
        self._selected_items = []
        # item → 其标注下拉框，方便在事件中查找对应 combo
        self._item_combos = {}
        # 信号抑制标记：在联动逻辑内部改动 checkbox 时避免重入
        self._suppress_signals = False
        self._build_ui()
        self._populate()

    # ------------------------------ UI ------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)

        # 顶部说明
        order_root_name = self.storage.order_root_folder if self.storage else "1订单"
        intro = QLabel(
            f"程序会扫描「<b>{order_root_name}/</b>」文件夹下的所有子文件夹。<br/>"
            "请勾选其中<b>属于业务员</b>的文件夹；每个文件夹旁边有一个"
            "<b>层级标注下拉框</b>，告诉程序这个文件夹是业务员、分公司还是应忽略。"
            "<br/>程序会根据文件夹下是否有子文件夹<b>自动判断默认标注</b>，"
            "多数情况下不需要手动改。<br/>"
            "勾选完成后点「确认导入」。"
        )
        intro.setWordWrap(True)
        # Neo-brutalism：柔紫背景 + 4px 黑色边框 + 直角
        intro.setStyleSheet(
            "QLabel { background:#C4B5FD; padding:10px 14px;"
            " border:4px solid #000000; border-radius:0px;"
            " color:#000000; font-weight:bold; }"
        )
        root.addWidget(intro)

        # 订单文件夹路径显示
        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("订单根文件夹："))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        path_row.addWidget(self.path_edit, 1)
        self.btn_browse = QPushButton("手动指定…")
        self.btn_browse.setObjectName("SecondaryButton")
        self.btn_browse.clicked.connect(self._browse_custom_order_root)
        path_row.addWidget(self.btn_browse)
        self.btn_rescan = QPushButton("重新扫描")
        self.btn_rescan.setObjectName("SecondaryButton")
        self.btn_rescan.clicked.connect(self._populate)
        path_row.addWidget(self.btn_rescan)
        root.addLayout(path_row)

        # 工具栏：全选、全不选、展开全部
        tools = QHBoxLayout()
        btn_check_all = QPushButton("全部勾选")
        btn_check_all.setObjectName("SecondaryButton")
        btn_check_all.clicked.connect(lambda: self._set_all_checked(True))
        btn_uncheck_all = QPushButton("全部取消")
        btn_uncheck_all.setObjectName("SecondaryButton")
        btn_uncheck_all.clicked.connect(lambda: self._set_all_checked(False))
        btn_expand = QPushButton("展开全部")
        btn_expand.setObjectName("SecondaryButton")
        btn_expand.clicked.connect(lambda: self.tree.expandAll())
        btn_collapse = QPushButton("折叠全部")
        btn_collapse.setObjectName("SecondaryButton")
        btn_collapse.clicked.connect(lambda: self.tree.collapseAll())
        tools.addWidget(btn_check_all)
        tools.addWidget(btn_uncheck_all)
        tools.addSpacing(20)
        tools.addWidget(btn_expand)
        tools.addWidget(btn_collapse)
        tools.addStretch(1)
        root.addLayout(tools)

        # 树：三列（文件夹名、层级标注、客户预览）
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["文件夹名", "层级标注", "预览：客户"])
        self.tree.setColumnWidth(0, 240)
        self.tree.setColumnWidth(1, 200)
        self.tree.itemChanged.connect(self._on_item_changed)
        root.addWidget(self.tree, 1)

        # 提示：识别规则（关键词从 config.json 读取）
        try:
            cfg = self.storage.load_config() if self.storage else {}
            kws = cfg.get("mid_layer_keywords", ["进行", "订单"])
        except Exception:
            kws = ["进行", "订单"]
        if kws:
            rule_tip_text = (
                "客户识别规则：若业务员文件夹下有匹配中间层关键词的子文件夹，"
                "将进入该文件夹抓取客户；否则把业务员下的子文件夹直接作为客户。"
                "中间层关键词可在「⚙ 高级设置」中配置。"
            )
        else:
            rule_tip_text = (
                "客户识别规则：当前未配置中间层关键词，"
                "程序会直接把业务员下的所有子文件夹作为客户。"
                "中间层关键词可在「⚙ 高级设置」中配置。"
            )
        rule_tip = QLabel(rule_tip_text)
        rule_tip.setWordWrap(True)
        # Neo-brutalism 禁用灰字，用纯黑 + 小字号
        rule_tip.setStyleSheet("color:#000000;font-size:12px;")
        root.addWidget(rule_tip)

        # 按钮
        btns = QDialogButtonBox()
        self.btn_ok = btns.addButton("确认导入", QDialogButtonBox.AcceptRole)
        self.btn_cancel = btns.addButton("取消", QDialogButtonBox.RejectRole)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    # --------------------- 数据填充 ---------------------
    def _populate(self):
        """扫描订单根文件夹并构建树"""
        self._suppress_signals = True
        self.tree.clear()
        self._item_combos.clear()
        self._order_root = ""

        if not self.storage.root_dir:
            QMessageBox.warning(self, "提示", "请先在首页设置并保存"
                                "「公司资料根目录」。")
            self._suppress_signals = False
            return

        default_order_root = os.path.join(
            self.storage.root_dir, self.storage.order_root_folder
        )
        if not os.path.isdir(default_order_root):
            # 提示用户手动选择
            ret = QMessageBox.question(
                self, f"未找到「{self.storage.order_root_folder}」文件夹",
                f"在根目录下没有找到「{self.storage.order_root_folder}」文件夹：\n"
                f"{default_order_root}\n\n是否手动指定订单根文件夹？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if ret == QMessageBox.Yes:
                self._suppress_signals = False
                self._browse_custom_order_root()
                return
            self._suppress_signals = False
            return

        self._order_root = default_order_root
        self.path_edit.setText(self._order_root)
        self._fill_tree_from_order_root()
        self._suppress_signals = False

    def _browse_custom_order_root(self):
        order_root_name = self.storage.order_root_folder if self.storage else "1订单"
        d = QFileDialog.getExistingDirectory(
            self, f"请选择订单根文件夹（通常名为 {order_root_name}）",
            self.storage.root_dir or ""
        )
        if not d:
            return
        self._order_root = d
        self.path_edit.setText(d)
        self._suppress_signals = True
        self.tree.clear()
        self._item_combos.clear()
        self._fill_tree_from_order_root()
        self._suppress_signals = False

    def _fill_tree_from_order_root(self):
        """按 self._order_root 扫描并填充树。支持两层：
           第 1 层 = 订单根文件夹 下的文件夹（可能是业务员，也可能是分公司）
           第 2 层 = 第 1 层文件夹的子文件夹（用于分公司内的业务员）
        """
        if not self._order_root or not os.path.isdir(self._order_root):
            return
        try:
            entries = sorted(os.listdir(self._order_root))
        except OSError as e:
            QMessageBox.warning(self, "错误", f"无法读取目录：{e}")
            return

        for name in entries:
            full = os.path.join(self._order_root, name)
            if not os.path.isdir(full) or name.startswith("."):
                continue
            # 预先统计子目录数量（决定默认标注）
            try:
                sub_names = sorted([
                    s for s in os.listdir(full)
                    if os.path.isdir(os.path.join(full, s))
                    and not s.startswith(".")
                ])
            except OSError:
                sub_names = []
            has_children = len(sub_names) > 0

            lvl1 = QTreeWidgetItem([name, "", ""])
            lvl1.setFlags(lvl1.flags() | Qt.ItemIsUserCheckable)
            lvl1.setCheckState(0, Qt.Unchecked)
            lvl1.setData(0, _ROLE_INFO,
                         {"rel_path": name, "abs": full, "level": 1})
            # 第 1 层客户预览
            lvl1.setText(2, self._customer_preview(name))
            self.tree.addTopLevelItem(lvl1)

            # 第 2 层：可能是分公司内的业务员
            for sub in sub_names:
                sub_full = os.path.join(full, sub)
                rel_sub = f"{name}/{sub}"
                lvl2 = QTreeWidgetItem([sub, "", ""])
                lvl2.setFlags(lvl2.flags() | Qt.ItemIsUserCheckable)
                lvl2.setCheckState(0, Qt.Unchecked)
                lvl2.setData(0, _ROLE_INFO,
                             {"rel_path": rel_sub, "abs": sub_full,
                              "level": 2})
                lvl2.setText(2, self._customer_preview(rel_sub))
                lvl1.addChild(lvl2)

            # 先给所有 item 挂标注下拉框（必须在 addTopLevelItem / addChild 之后
            # 才能 setItemWidget），再根据默认值触发联动初始化勾选状态
            self._attach_combo(lvl1, LEVEL1_OPTIONS)
            for j in range(lvl1.childCount()):
                self._attach_combo(lvl1.child(j), LEVEL2_OPTIONS)

            # 设置默认标注并触发一次联动，保持"不碰下拉框即与旧版行为一致"
            default_label = LABEL_BRANCH if has_children else LABEL_SALESPERSON
            self._set_item_label(lvl1, default_label)

        self.tree.expandToDepth(0)

    def _attach_combo(self, item: QTreeWidgetItem, options):
        """给一个 item 的第 2 列挂上标注下拉框"""
        combo = QComboBox()
        combo.addItems(options)
        # 默认第一项；真正的默认值由 _set_item_label 在挂完所有 combo 之后设置
        combo.setCurrentIndex(0)
        # 用闭包把 item 绑进来
        combo.currentTextChanged.connect(
            lambda text, it=item: self._on_label_changed(it, text)
        )
        self.tree.setItemWidget(item, 1, combo)
        self._item_combos[id(item)] = combo

    def _get_combo(self, item: QTreeWidgetItem):
        return self._item_combos.get(id(item))

    def _get_label(self, item: QTreeWidgetItem) -> str:
        combo = self._get_combo(item)
        return combo.currentText() if combo else ""

    def _set_item_label(self, item: QTreeWidgetItem, label: str):
        """把某个 item 的标注设置为 label，自动触发联动。
        （通过改 combo 的 currentText 触发 currentTextChanged）"""
        combo = self._get_combo(item)
        if not combo:
            return
        if combo.currentText() == label:
            # 即使相同也主动触发一次，保证初始联动到位
            self._on_label_changed(item, label)
        else:
            combo.setCurrentText(label)

    def _customer_preview(self, rel_under_order_root: str) -> str:
        """根据扫描规则，预览将作为客户导入的数量及前几项（仅展示，不改数据）"""
        try:
            mid, customers = self.storage.scan_customers_for(rel_under_order_root)
        except Exception:
            return ""
        if not customers:
            return "（无客户子文件夹）"
        sample = "、".join(customers[:3])
        more = f" …共 {len(customers)} 个" if len(customers) > 3 else ""
        mid_str = f"【中间层：{mid}】 " if mid else ""
        return f"{mid_str}{sample}{more}"

    # --------------------- 交互：标注 ↔ 勾选 联动 ---------------------
    def _on_label_changed(self, item: QTreeWidgetItem, label: str):
        """当某个 item 的标注下拉框变化时，自动调整勾选状态。

        规则（第 1 层）：
          - "业务员"           → 勾选自身，取消所有子节点
          - "分公司/区域"      → 取消自身，勾选所有子节点（子节点标注 = 业务员）
          - "忽略"             → 取消自身，取消所有子节点

        规则（第 2 层）：
          - "业务员" → 勾选自身
          - "忽略"   → 取消自身
        """
        if self._suppress_signals:
            return
        info = item.data(0, _ROLE_INFO) or {}
        level = info.get("level", 1)

        self._suppress_signals = True
        try:
            if level == 1:
                if label == LABEL_SALESPERSON:
                    item.setCheckState(0, Qt.Checked)
                    for j in range(item.childCount()):
                        c = item.child(j)
                        c.setCheckState(0, Qt.Unchecked)
                        # 子标注无所谓，用户没必要展开；默认保持"业务员"即可
                elif label == LABEL_BRANCH:
                    item.setCheckState(0, Qt.Unchecked)
                    for j in range(item.childCount()):
                        c = item.child(j)
                        # 子节点默认标注 = 业务员，联动勾选；需手动触发
                        self._set_item_label(c, LABEL_SALESPERSON)
                elif label == LABEL_IGNORE:
                    item.setCheckState(0, Qt.Unchecked)
                    for j in range(item.childCount()):
                        c = item.child(j)
                        c.setCheckState(0, Qt.Unchecked)
            else:  # level == 2
                if label == LABEL_SALESPERSON:
                    item.setCheckState(0, Qt.Checked)
                elif label == LABEL_IGNORE:
                    item.setCheckState(0, Qt.Unchecked)
        finally:
            self._suppress_signals = False

    def _on_item_changed(self, item, column):
        """用户手动改 checkbox 时，保持与标注的一致性。

        - 第 1 层：若当前标注为"分公司"但父 checkbox 被勾上 → 自动改标注为"业务员"；
                  若标注为"忽略"但父 checkbox 被勾上 → 自动改标注为"业务员"。
        - 第 2 层：若标注为"忽略"但 checkbox 被勾上 → 自动改标注为"业务员"。
        (取消 checkbox 的时候不强制改标注，避免干扰)
        """
        if column != 0 or self._suppress_signals:
            return
        info = item.data(0, _ROLE_INFO) or {}
        level = info.get("level", 1)
        checked = item.checkState(0) == Qt.Checked
        if not checked:
            return

        current_label = self._get_label(item)
        self._suppress_signals = True
        try:
            if level == 1:
                if current_label in (LABEL_BRANCH, LABEL_IGNORE):
                    # 手动勾上父节点 → 按"业务员"对待
                    combo = self._get_combo(item)
                    if combo:
                        combo.setCurrentText(LABEL_SALESPERSON)
                    # combo 变化会触发 _on_label_changed，但我们在
                    # suppress 期间，需要手动执行一次等效逻辑：
                    for j in range(item.childCount()):
                        item.child(j).setCheckState(0, Qt.Unchecked)
            else:
                # 第 2 层：勾上 → 标注应为业务员
                if current_label == LABEL_IGNORE:
                    combo = self._get_combo(item)
                    if combo:
                        combo.setCurrentText(LABEL_SALESPERSON)
                # 勾了子节点，同层的父节点若勾着则取消
                parent = item.parent()
                if parent is not None and parent.checkState(0) == Qt.Checked:
                    parent.setCheckState(0, Qt.Unchecked)
                    # 父节点由"业务员"改成"分公司"
                    pcombo = self._get_combo(parent)
                    if pcombo and pcombo.currentText() == LABEL_SALESPERSON:
                        pcombo.setCurrentText(LABEL_BRANCH)
        finally:
            self._suppress_signals = False

    def _set_all_checked(self, checked: bool):
        """全部勾选 / 全部取消 —— 通过改标注触发联动，保持语义一致。"""
        self._suppress_signals = True
        try:
            for i in range(self.tree.topLevelItemCount()):
                top = self.tree.topLevelItem(i)
                if not checked:
                    # 全不选：父、子标注统一改为"忽略"
                    tcombo = self._get_combo(top)
                    if tcombo:
                        tcombo.setCurrentText(LABEL_IGNORE)
                    top.setCheckState(0, Qt.Unchecked)
                    for j in range(top.childCount()):
                        c = top.child(j)
                        ccombo = self._get_combo(c)
                        if ccombo:
                            ccombo.setCurrentText(LABEL_IGNORE)
                        c.setCheckState(0, Qt.Unchecked)
                else:
                    # 全选：有子则父=分公司/子=业务员；无子则父=业务员
                    if top.childCount() > 0:
                        tcombo = self._get_combo(top)
                        if tcombo:
                            tcombo.setCurrentText(LABEL_BRANCH)
                        top.setCheckState(0, Qt.Unchecked)
                        for j in range(top.childCount()):
                            c = top.child(j)
                            ccombo = self._get_combo(c)
                            if ccombo:
                                ccombo.setCurrentText(LABEL_SALESPERSON)
                            c.setCheckState(0, Qt.Checked)
                    else:
                        tcombo = self._get_combo(top)
                        if tcombo:
                            tcombo.setCurrentText(LABEL_SALESPERSON)
                        top.setCheckState(0, Qt.Checked)
        finally:
            self._suppress_signals = False

    # --------------------- 确认 ---------------------
    def _on_accept(self):
        """按标注 + 勾选状态收集结果。

        规则：
          - 第 1 层标注=业务员 且已勾选 → 导入 rel_path=该文件夹名
          - 第 1 层标注=分公司/区域 → 遍历其子，标注=业务员 且已勾选 的子作为业务员导入
          - 第 1 层标注=忽略 → 跳过（以及其下所有子节点）
        """
        selected = []
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            top_label = self._get_label(top)
            top_info = top.data(0, _ROLE_INFO) or {}

            if top_label == LABEL_IGNORE:
                continue

            if top_label == LABEL_SALESPERSON:
                if top.checkState(0) == Qt.Checked:
                    selected.append({
                        "name": top.text(0),
                        "rel_path": top_info.get("rel_path", top.text(0)),
                    })
                continue

            if top_label == LABEL_BRANCH:
                for j in range(top.childCount()):
                    c = top.child(j)
                    c_label = self._get_label(c)
                    if c_label != LABEL_SALESPERSON:
                        continue
                    if c.checkState(0) != Qt.Checked:
                        continue
                    c_info = c.data(0, _ROLE_INFO) or {}
                    selected.append({
                        "name": c.text(0),
                        "rel_path": c_info.get("rel_path", c.text(0)),
                    })
                continue

            # 防御：未知标注 → 按旧行为兜底
            if top.checkState(0) == Qt.Checked:
                selected.append({
                    "name": top.text(0),
                    "rel_path": top_info.get("rel_path", top.text(0)),
                })

        if not selected:
            QMessageBox.information(self, "提示", "还没有勾选任何业务员文件夹。")
            return

        # 去重（按 rel_path）
        seen = set()
        uniq = []
        for s in selected:
            if s["rel_path"] in seen:
                continue
            seen.add(s["rel_path"])
            uniq.append(s)

        self._selected_rel_paths = [s["rel_path"] for s in uniq]
        self._selected_items = uniq
        self.accept()

    # --------------------- 对外 ---------------------
    def get_selected_rel_paths(self):
        return list(self._selected_rel_paths)

    def get_selected_items(self):
        return list(getattr(self, "_selected_items", []))
