# -*- coding: utf-8 -*-
"""启动页（首页） —— Neo-brutalism 视觉适配。

本轮改造要点（仅视觉与交互）：
- 配置区、模式选择区、底部工具栏三块卡片改用
  :class:`app.widgets.neo_shadow_frame.NeoShadowFrame` 替代原
  ``QFrame``，自带硬偏移黑阴影；
- 主按钮（"📝 单笔创建" / "📦 批量导入"）使用 ``BigButton`` 对象名，
  次级按钮（底部工具栏）使用 ``SecondaryButton``，保持与全局 QSS 一致；
- 去掉灰色分隔线，改为纯黑粗线 (4px / COLOR_INK)；
- 顶部补充一段说明文字引导用户完成首次配置；
- 扫描导入：在订单根目录不存在或为空时给出友好提示；
  用户未勾选任何扫描结果时同样提示。
"""

import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget
)

from ..style import COLOR_INK
from ..widgets import NeoShadowFrame


class HomePage(QWidget):
    """启动页：设置根目录、模板目录、选择功能"""

    # 信号
    request_single = pyqtSignal()
    request_batch = pyqtSignal()
    request_templates = pyqtSignal()
    request_history = pyqtSignal()
    request_help = pyqtSignal()
    salespersons_changed = pyqtSignal()
    root_dir_changed = pyqtSignal(str)
    template_dir_changed = pyqtSignal(str)
    # 高级设置保存后触发，通知主窗口刷新相关页面
    config_changed = pyqtSignal()

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self._build_ui()
        self._load_initial()

    # -------- UI 构建 --------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(18)

        # 标题
        title = QLabel("订单文件夹自动创建工具")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("一键生成标准订单目录结构 · 自动复制模板文件 · 生成文件清单")
        subtitle.setObjectName("SubTitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 顶部简要引导文字：向首次使用的用户解释整体流程
        intro = QLabel(
            "① 先设置公司资料根目录 → ② 可选设置模板文件目录 → "
            "③ 进入「单笔创建」或「批量导入」即可自动生成订单文件夹。"
            "更多功能可在「❓ 使用帮助」查看。"
        )
        intro.setWordWrap(True)
        intro.setAlignment(Qt.AlignCenter)
        intro.setStyleSheet("color:#000000; font-weight:bold;")
        layout.addWidget(intro)

        # ============== 配置区卡片（NeoShadowFrame） ==============
        config_frame = NeoShadowFrame()
        cfg_layout = QGridLayout(config_frame)
        cfg_layout.setContentsMargins(20, 20, 20, 20)
        cfg_layout.setHorizontalSpacing(10)
        cfg_layout.setVerticalSpacing(12)

        # 根目录
        lbl1 = QLabel("公司资料根目录：")
        lbl1.setObjectName("SectionLabel")
        self.root_edit = QLineEdit()
        self.root_edit.setPlaceholderText("请设置公司资料存放的根目录（必填）")
        self.root_edit.setReadOnly(False)
        btn_browse_root = QPushButton("浏览…")
        btn_browse_root.setObjectName("SecondaryButton")
        btn_browse_root.clicked.connect(self._browse_root)
        btn_save_root = QPushButton("保存")
        btn_save_root.clicked.connect(self._save_root)

        cfg_layout.addWidget(lbl1, 0, 0)
        cfg_layout.addWidget(self.root_edit, 0, 1)
        cfg_layout.addWidget(btn_browse_root, 0, 2)
        cfg_layout.addWidget(btn_save_root, 0, 3)

        # 模板目录
        lbl2 = QLabel("模板文件目录：")
        lbl2.setObjectName("SectionLabel")
        self.tpl_edit = QLineEdit()
        self.tpl_edit.setPlaceholderText(
            "存放模板文件的目录（可选，按「产地/文件」的子目录结构组织）")
        btn_browse_tpl = QPushButton("浏览…")
        btn_browse_tpl.setObjectName("SecondaryButton")
        btn_browse_tpl.clicked.connect(self._browse_tpl)
        btn_save_tpl = QPushButton("保存")
        btn_save_tpl.clicked.connect(self._save_tpl)

        cfg_layout.addWidget(lbl2, 1, 0)
        cfg_layout.addWidget(self.tpl_edit, 1, 1)
        cfg_layout.addWidget(btn_browse_tpl, 1, 2)
        cfg_layout.addWidget(btn_save_tpl, 1, 3)

        tip = QLabel(
            "提示：模板目录的子目录名称需与「⚙ 高级设置」中的产地配置保持一致；"
            "若未设置模板目录，将跳过模板文件复制步骤。"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#000000;")
        cfg_layout.addWidget(tip, 2, 1, 1, 3)

        layout.addWidget(config_frame)

        # ============== 模式选择区卡片（NeoShadowFrame） ==============
        mode_card = NeoShadowFrame()
        mode_inner = QVBoxLayout(mode_card)
        mode_inner.setContentsMargins(20, 20, 20, 20)
        mode_inner.setSpacing(8)

        mode_title = QLabel("请选择创建方式")
        mode_title.setAlignment(Qt.AlignCenter)
        mode_title.setStyleSheet("font-weight:bold; font-size:16px;")
        mode_inner.addWidget(mode_title)

        mode_desc = QLabel(
            "单笔创建适合逐单填写；批量导入可通过 Excel 一次性生成多笔订单文件夹。"
        )
        mode_desc.setAlignment(Qt.AlignCenter)
        mode_desc.setWordWrap(True)
        mode_desc.setStyleSheet("color:#000000;")
        mode_inner.addWidget(mode_desc)

        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(30)
        mode_layout.setAlignment(Qt.AlignCenter)

        self.btn_single = QPushButton("📝 单笔创建")
        self.btn_single.setObjectName("BigButton")
        self.btn_single.clicked.connect(self._click_single)

        self.btn_batch = QPushButton("📦 批量导入")
        self.btn_batch.setObjectName("BigButton")
        self.btn_batch.clicked.connect(self._click_batch)

        mode_layout.addStretch(1)
        mode_layout.addWidget(self.btn_single)
        mode_layout.addWidget(self.btn_batch)
        mode_layout.addStretch(1)
        mode_inner.addLayout(mode_layout)

        layout.addWidget(mode_card)

        # 分隔线：Neo-brutalism 风格的 4px 纯黑硬线
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(4)
        divider.setStyleSheet(f"background:{COLOR_INK}; border:none;")
        layout.addWidget(divider)

        # ============== 底部工具栏卡片（NeoShadowFrame） ==============
        bottom_card = NeoShadowFrame()
        bottom_inner = QVBoxLayout(bottom_card)
        bottom_inner.setContentsMargins(16, 14, 16, 14)
        bottom_inner.setSpacing(6)

        bottom_title = QLabel("更多功能")
        bottom_title.setStyleSheet("font-weight:bold; font-size:14px;")
        bottom_inner.addWidget(bottom_title)

        bottom = QHBoxLayout()
        bottom.setAlignment(Qt.AlignCenter)

        self.btn_scan = QPushButton("🧭 扫描导入业务员")
        self.btn_scan.setObjectName("SecondaryButton")
        self.btn_scan.clicked.connect(self._click_scan_import)

        self.btn_cleanup = QPushButton("🧹 整理已有订单文件夹")
        self.btn_cleanup.setObjectName("SecondaryButton")
        self.btn_cleanup.clicked.connect(self._click_cleanup)

        self.btn_templates = QPushButton("🗂 模板管理")
        self.btn_templates.setObjectName("SecondaryButton")
        self.btn_templates.clicked.connect(self.request_templates.emit)

        self.btn_history = QPushButton("🕘 历史记录")
        self.btn_history.setObjectName("SecondaryButton")
        self.btn_history.clicked.connect(self.request_history.emit)

        self.btn_help = QPushButton("❓ 使用帮助")
        self.btn_help.setObjectName("SecondaryButton")
        self.btn_help.clicked.connect(self.request_help.emit)

        self.btn_advanced = QPushButton("⚙ 高级设置")
        self.btn_advanced.setObjectName("SecondaryButton")
        self.btn_advanced.clicked.connect(self._click_advanced_settings)

        # 底部按钮等宽整齐
        for _b in (self.btn_scan, self.btn_cleanup, self.btn_templates,
                   self.btn_history, self.btn_help, self.btn_advanced):
            _b.setMinimumWidth(150)
            _b.setMinimumHeight(40)

        bottom.addStretch(1)
        bottom.addWidget(self.btn_scan)
        bottom.addSpacing(12)
        bottom.addWidget(self.btn_cleanup)
        bottom.addSpacing(12)
        bottom.addWidget(self.btn_templates)
        bottom.addSpacing(12)
        bottom.addWidget(self.btn_history)
        bottom.addSpacing(12)
        bottom.addWidget(self.btn_help)
        bottom.addSpacing(12)
        bottom.addWidget(self.btn_advanced)
        bottom.addStretch(1)
        bottom_inner.addLayout(bottom)

        layout.addWidget(bottom_card)
        layout.addStretch(1)

    # -------- 数据加载 --------
    def _load_initial(self):
        if self.storage.root_dir:
            self.root_edit.setText(self.storage.root_dir)
            cfg = self.storage.load_config()
            self.tpl_edit.setText(cfg.get("template_files_dir", ""))
        self._refresh_mode_buttons_enabled()

    def refresh(self):
        """外部切换回本页时调用"""
        self._load_initial()

    # -------- 事件 --------
    def _browse_root(self):
        d = QFileDialog.getExistingDirectory(self, "选择公司资料根目录",
                                             self.root_edit.text() or "")
        if d:
            self.root_edit.setText(d)

    def _browse_tpl(self):
        d = QFileDialog.getExistingDirectory(self, "选择模板文件目录",
                                             self.tpl_edit.text() or "")
        if d:
            self.tpl_edit.setText(d)

    def _save_root(self):
        root = self.root_edit.text().strip()
        if not root:
            QMessageBox.warning(self, "提示", "请先选择根目录")
            return
        if not os.path.isdir(root):
            try:
                os.makedirs(root, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "提示", f"目录不存在且创建失败：{e}")
                return

        # Bug 14：在切换根目录前，保存旧配置中的关键自定义字段（如
        # 用户通过向导或「⚙ 高级设置」配置的 origin_map、
        # order_root_folder 等）。这样切换到一个从未使用过的新目录时，
        # set_root_dir 会写入硬编码默认值，但随后把旧配置迁移过来，
        # 避免用户精心配置的自定义项目被硬编码默认值覆盖。
        #
        # 关键：只有在目标目录尚不存在 .order_tool/config.json 时才迁移，
        # 否则会把自己的旧配置覆盖掉目标目录里本来就有的配置（用户可能
        # 在多个根目录间切换，每个目录都应保留各自的配置）。
        old_cfg = self.storage.load_config() if self.storage.config_file else {}
        from pathlib import Path
        new_cfg_path = Path(root) / ".order_tool" / "config.json"
        new_dir_is_fresh = not new_cfg_path.exists()

        self.storage.set_root_dir(root)

        # 仅当目标目录是全新目录（set_root_dir 刚用默认值创建了 config.json）
        # 时，把旧配置中非空的关键字段迁移过来。
        if old_cfg and new_dir_is_fresh:
            new_cfg = self.storage.load_config()
            migrated = False
            for key in ("order_root_folder", "mid_layer_keywords",
                        "origin_map", "origin_file_ext"):
                if key in old_cfg and old_cfg[key]:
                    new_cfg[key] = old_cfg[key]
                    migrated = True
            if migrated:
                self.storage.save_config(new_cfg)

        # 同步保存到 bootstrap
        from ..core.storage import save_bootstrap, load_bootstrap
        bs = load_bootstrap()
        bs["last_root"] = root
        save_bootstrap(bs)
        self.root_dir_changed.emit(root)
        # 如果之前有模板目录设置，保持
        cfg = self.storage.load_config()
        if self.tpl_edit.text().strip():
            cfg["template_files_dir"] = self.tpl_edit.text().strip()
            self.storage.save_config(cfg)
        else:
            self.tpl_edit.setText(cfg.get("template_files_dir", ""))
        self._refresh_mode_buttons_enabled()
        QMessageBox.information(self, "成功", "根目录已保存。")

    def _save_tpl(self):
        if not self.storage.root_dir:
            QMessageBox.warning(self, "提示", "请先设置根目录")
            return
        tpl = self.tpl_edit.text().strip()
        self.storage.update_config(template_files_dir=tpl)
        self.template_dir_changed.emit(tpl)
        QMessageBox.information(self, "成功",
                                "模板文件目录已保存。" if tpl else "已清空模板文件目录（将跳过模板文件复制）。")

    def _click_single(self):
        if not self._check_root():
            return
        self._auto_save_root_if_needed()
        self.request_single.emit()

    def _click_batch(self):
        if not self._check_root():
            return
        self._auto_save_root_if_needed()
        self.request_batch.emit()

    def _click_scan_import(self):
        """扫描订单根目录下的业务员/客户结构。

        本轮新增友好提示：
        - 若订单根目录不存在或为空，提醒用户先整理订单目录；
        - 若用户未勾选任何文件夹，提示"未选择任何业务员"而不是静默返回。
        """
        if not self._check_root():
            return
        self._auto_save_root_if_needed()

        # 先检查订单根目录是否存在且非空，否则弹出友好提示
        order_root = os.path.join(
            self.storage.root_dir, self.storage.order_root_folder
        )
        if not os.path.isdir(order_root):
            QMessageBox.information(
                self, "暂无可扫描内容",
                f"未找到订单根目录：\n{order_root}\n\n"
                "请先在该根目录下创建「订单根文件夹」"
                "（默认为"
                f" {self.storage.order_root_folder}），"
                "并将业务员/客户文件夹整理到其中。"
            )
            return
        try:
            items = [n for n in os.listdir(order_root)
                     if os.path.isdir(os.path.join(order_root, n))]
        except Exception as e:
            QMessageBox.warning(self, "提示", f"读取订单根目录失败：{e}")
            return
        if not items:
            QMessageBox.information(
                self, "暂无可扫描内容",
                f"订单根目录「{order_root}」下没有业务员文件夹。\n\n"
                "请先将业务员/客户文件夹放入该目录后再扫描。"
            )
            return

        from ..dialogs.scan_import import ScanImportDialog
        dlg = ScanImportDialog(self.storage, parent=self)
        if dlg.exec_() != dlg.Accepted:
            return
        rel_paths = dlg.get_selected_rel_paths()
        if not rel_paths:
            QMessageBox.information(
                self, "提示",
                "未选择任何业务员文件夹。若需导入，请在扫描结果中勾选后再点击确定。"
            )
            return
        # 询问是否覆盖已有同名业务员
        overwrite = False
        existing_names = {it["name"] for it in self.storage.load_salespersons()}
        about_to_overlap = [p.split("/")[-1] for p in rel_paths
                            if p.split("/")[-1] in existing_names]
        if about_to_overlap:
            ret = QMessageBox.question(
                self, "已存在的业务员",
                "以下业务员已存在，是否用扫描结果<b>合并/更新</b>它们的"
                "路径和客户列表？<br/><br/>"
                + "、".join(about_to_overlap[:10])
                + ("…" if len(about_to_overlap) > 10 else ""),
                QMessageBox.Yes | QMessageBox.No,
            )
            overwrite = (ret == QMessageBox.Yes)
        summary = self.storage.import_scanned_salespersons(
            rel_paths, overwrite=overwrite
        )
        self.salespersons_changed.emit()
        QMessageBox.information(
            self, "导入完成",
            f"新增业务员：{len(summary['added'])} 名\n"
            f"更新业务员：{len(summary['updated'])} 名\n"
            f"跳过（已存在且未覆盖）：{len(summary['skipped'])} 名"
        )

    def _check_root(self) -> bool:
        if not self.storage.root_dir:
            QMessageBox.warning(self, "提示", "请先设置并保存根目录")
            return False
        return True

    def _auto_save_root_if_needed(self):
        """如果输入框中根目录和当前不一致，自动保存"""
        cur = self.root_edit.text().strip()
        if cur and cur != self.storage.root_dir:
            self._save_root()

    def _refresh_mode_buttons_enabled(self):
        ok = bool(self.storage.root_dir)
        self.btn_single.setEnabled(ok)
        self.btn_batch.setEnabled(ok)
        self.btn_scan.setEnabled(ok)
        self.btn_cleanup.setEnabled(ok)
        self.btn_templates.setEnabled(ok)
        self.btn_history.setEnabled(ok)
        # 帮助页面不需要根目录，始终可点
        self.btn_help.setEnabled(True)
        # 高级设置需要先设置根目录（config.json 才有地方写）
        if hasattr(self, "btn_advanced"):
            self.btn_advanced.setEnabled(ok)

    # -------- 高级设置 --------
    def _click_advanced_settings(self):
        if not self._check_root():
            return
        self._auto_save_root_if_needed()
        from ..dialogs.advanced_settings import AdvancedSettingsDialog
        dlg = AdvancedSettingsDialog(self.storage, parent=self)
        if dlg.exec_() == dlg.Accepted:
            # 通知主窗口刷新相关页面（例如产品类别下拉框）
            self.config_changed.emit()

    # -------- 整理已有订单文件夹（功能 D） --------
    def _click_cleanup(self):
        if not self._check_root():
            return
        self._auto_save_root_if_needed()

        from PyQt5.QtWidgets import (
            QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QPushButton
        )
        from ..core import folder_builder
        from ..dialogs.folder_cleanup import FolderCleanupDialog
        # Bug 26/30：对话框中的下拉框统一使用 StyledComboBox，
        # 与全局 Neo-brutalism 视觉保持一致
        from ..widgets import StyledComboBox

        dlg = QDialog(self)
        dlg.setWindowTitle("整理已有订单文件夹")
        # Bug 30：新增业务员字段后略微加高对话框
        dlg.resize(560, 360)
        form = QFormLayout(dlg)

        # 订单文件夹路径
        h_path = QHBoxLayout()
        edit_folder = QLineEdit()
        edit_folder.setPlaceholderText("选择要整理的订单文件夹…")
        btn_pick = QPushButton("浏览…")

        def _pick():
            d = QFileDialog.getExistingDirectory(
                dlg, "选择订单文件夹", edit_folder.text() or self.storage.root_dir or ""
            )
            if d:
                edit_folder.setText(d)
                # 自动根据文件夹名填订单号
                base = d.rstrip("/\\").split("/")[-1].split("\\")[-1]
                if base and not edit_order_no.text().strip():
                    edit_order_no.setText(base)
        btn_pick.clicked.connect(_pick)
        h_path.addWidget(edit_folder, 1)
        h_path.addWidget(btn_pick)
        w_path = QWidget()
        w_path.setLayout(h_path)
        form.addRow("订单文件夹：", w_path)

        # 订单号
        edit_order_no = QLineEdit()
        edit_order_no.setPlaceholderText("例如 ORD-2026001")
        form.addRow("订单号：", edit_order_no)

        # Bug 30：新增业务员下拉框。此前 salesperson 固定为空串，
        # 会导致模板文件名中的 <业务员> 占位符被替换为空串，
        # 让 FolderCleanupDialog 的"期望文件名"与实际文件名不一致。
        cmb_salesperson = StyledComboBox(searchable=True)
        sp_names = [it["name"] for it in self.storage.load_salespersons()]
        cmb_salesperson.addItems(["（不选择）"] + sp_names)
        form.addRow("业务员：", cmb_salesperson)

        # 客户名称
        edit_customer = QLineEdit()
        edit_customer.setPlaceholderText("用于替换 <客户名称> 占位符")
        form.addRow("客户名称：", edit_customer)

        # 模板选择（Bug 26：替换为 StyledComboBox 保持视觉一致）
        cmb_template = StyledComboBox()
        tpl_list = self.storage.list_template_files()
        tpl_entries = []
        for fn in tpl_list.get("standard", []):
            tpl = self.storage.load_template(fn)
            if tpl:
                tpl_entries.append((f"[标准] {tpl.get('display_name', fn)}", fn))
        for fn in tpl_list.get("salesperson", []):
            tpl = self.storage.load_template(fn)
            if tpl:
                tpl_entries.append((f"[业务员] {tpl.get('display_name', fn)}", fn))
        for fn in tpl_list.get("customer", []):
            tpl = self.storage.load_template(fn)
            if tpl:
                tpl_entries.append((f"[客户] {tpl.get('display_name', fn)}", fn))
        for label, _ in tpl_entries:
            cmb_template.addItem(label)
        form.addRow("使用模板：", cmb_template)

        # 产品类别（从 config.json 的 origin_map 动态读取）
        # Bug 26：替换为 StyledComboBox 保持视觉一致
        cmb_cat = StyledComboBox()
        cfg_home = self.storage.load_config() if self.storage else {}
        cat_opts = list((cfg_home.get("origin_map") or {}).keys())
        if cat_opts:
            cmb_cat.addItems(cat_opts)
        form.addRow("产品类别：", cmb_cat)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)

        if dlg.exec_() != dlg.Accepted:
            return

        order_folder = edit_folder.text().strip()
        order_no = edit_order_no.text().strip()
        customer = edit_customer.text().strip()
        idx = cmb_template.currentIndex()

        # Bug 30：获取用户选择的业务员。"（不选择）" 对应空串，
        # 让 <业务员> 占位符被替换为空（用户明确选择不带业务员）。
        sp_text = cmb_salesperson.currentText().strip()
        if sp_text == "（不选择）":
            sp_text = ""

        if not order_folder or not os.path.isdir(order_folder):
            QMessageBox.warning(self, "提示", "请选择一个存在的订单文件夹")
            return
        if not order_no:
            QMessageBox.warning(self, "提示", "请填写订单号")
            return
        if idx < 0 or idx >= len(tpl_entries):
            QMessageBox.warning(self, "提示", "请选择一个模板")
            return

        tpl_fn = tpl_entries[idx][1]
        template = self.storage.load_template(tpl_fn)
        if not template:
            QMessageBox.warning(self, "提示", f"模板 {tpl_fn} 读取失败")
            return

        order = {
            "order_no": order_no,
            "customer": customer,
            "product_info": "",
            "po_no": "",
            "product_category": cmb_cat.currentText(),
            # Bug 30：使用用户选择的业务员名称（可能为空）
            "salesperson": sp_text,
            "needs_inspection": False,
            "order_type": "外贸" if template.get("type") == "export" else "内贸",
        }
        ctx = folder_builder.build_context(order)

        cfg_cleanup = self.storage.load_config()
        FolderCleanupDialog(
            order_folder_path=order_folder,
            order_no=order_no,
            template=template,
            ctx=ctx,
            parent=self,
            product_category=order["product_category"],
            needs_inspection=False,
            origin_map=cfg_cleanup.get("origin_map") or {},
            origin_file_ext=cfg_cleanup.get("origin_file_ext") or {},
        ).exec_()
