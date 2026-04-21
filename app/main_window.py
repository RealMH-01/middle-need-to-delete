# -*- coding: utf-8 -*-
"""主窗口：用 QStackedWidget 承载 5 个业务页面 + 一个 QDockWidget 承载帮助面板。

首次启动时（检测不到 bootstrap 记录）会弹出
:class:`~app.dialogs.setup_wizard.SetupWizard` 引导用户完成初始化。
"""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDockWidget, QMainWindow, QStackedWidget

from .core.storage import Storage, load_bootstrap, save_bootstrap
from .pages.home_page import HomePage
from .pages.single_page import SinglePage
from .pages.batch_page import BatchPage
from .pages.templates_page import TemplatesPage
from .pages.history_page import HistoryPage
from .pages.help_page import HelpPage


PAGE_HOME = 0
PAGE_SINGLE = 1
PAGE_BATCH = 2
PAGE_TEMPLATES = 3
PAGE_HISTORY = 4
# 注：帮助页面改由 QDockWidget 承载，不再是 QStackedWidget 的索引。


def _should_skip_wizard() -> bool:
    """判断是否跳过首次启动向导。

    - ``ORDER_TOOL_SKIP_WIZARD=1`` 环境变量：强制跳过（供自动化 / 测试使用）。
    - Qt 平台为 ``offscreen``：说明是无 GUI 的自动化测试环境，跳过向导。
    """
    if os.environ.get("ORDER_TOOL_SKIP_WIZARD") == "1":
        return True
    try:
        app = QApplication.instance()
        if app is not None and app.platformName() == "offscreen":
            return True
    except Exception:
        pass
    return False


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("订单文件夹自动创建工具")
        self.resize(1180, 760)

        # ------------------------------------------------------------
        # 1) 初始化 Storage —— 若无 bootstrap 记录则先跑向导
        # ------------------------------------------------------------
        bs = load_bootstrap()
        last_root = bs.get("last_root", "")

        if not last_root and not _should_skip_wizard():
            # 全新安装：弹出向导
            from .dialogs.setup_wizard import SetupWizard
            wizard = SetupWizard()  # parent 传 None（本窗口尚未 show）
            if wizard.exec_() != wizard.Accepted:
                # 用户主动退出向导：结束整个程序
                sys.exit(0)
            wizard_cfg = wizard.collected_config()
            self.storage = Storage()
            self.storage.set_root_dir(
                wizard_cfg["root_dir"], wizard_config=wizard_cfg
            )
            save_bootstrap({"last_root": wizard_cfg["root_dir"]})
        else:
            # 老用户 or 测试环境：按旧逻辑初始化
            self.storage = Storage(last_root if last_root else None)

        # ------------------------------------------------------------
        # 2) 页面与 StackedWidget
        # ------------------------------------------------------------
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.page_home = HomePage(self.storage)
        self.page_single = SinglePage(self.storage)
        self.page_batch = BatchPage(self.storage)
        self.page_templates = TemplatesPage(self.storage)
        self.page_history = HistoryPage(self.storage)
        self.page_help = HelpPage()

        self.stack.addWidget(self.page_home)
        self.stack.addWidget(self.page_single)
        self.stack.addWidget(self.page_batch)
        self.stack.addWidget(self.page_templates)
        self.stack.addWidget(self.page_history)
        # 注意：page_help 不再 addWidget 到 stack，而是放进 QDockWidget

        # ------------------------------------------------------------
        # 3) 帮助面板：QDockWidget，默认隐藏，停靠在右侧
        # ------------------------------------------------------------
        self.help_dock = QDockWidget("使用帮助", self)
        self.help_dock.setAllowedAreas(
            Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea
        )
        self.help_dock.setFeatures(
            QDockWidget.DockWidgetClosable
            | QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
        )
        self.help_dock.setMinimumWidth(380)
        self.help_dock.setWidget(self.page_help)
        self.help_dock.setVisible(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.help_dock)

        # ------------------------------------------------------------
        # 4) 事件绑定
        # ------------------------------------------------------------
        self.page_home.request_single.connect(lambda: self._goto(PAGE_SINGLE))
        self.page_home.request_batch.connect(lambda: self._goto(PAGE_BATCH))
        self.page_home.request_templates.connect(lambda: self._goto(PAGE_TEMPLATES))
        self.page_home.request_history.connect(lambda: self._goto(PAGE_HISTORY))
        self.page_home.request_help.connect(self._toggle_help)
        self.page_home.salespersons_changed.connect(self._on_salespersons_changed)
        self.page_home.root_dir_changed.connect(self._on_root_changed)
        self.page_home.config_changed.connect(self._on_config_changed)

        self.page_single.request_back.connect(lambda: self._goto(PAGE_HOME))
        self.page_batch.request_back.connect(lambda: self._goto(PAGE_HOME))
        self.page_templates.request_back.connect(lambda: self._goto(PAGE_HOME))
        self.page_history.request_back.connect(lambda: self._goto(PAGE_HOME))
        # 帮助页面不再有"返回首页"信号 —— 通过 DockWidget 的关闭按钮自行隐藏

        self.stack.setCurrentIndex(PAGE_HOME)

        # 状态栏
        self.statusBar().showMessage("就绪")
        if self.storage and self.storage.root_dir:
            self.statusBar().showMessage(f"根目录：{self.storage.root_dir}")

    # ------------------------------------------------------------------
    # 帮助面板切换 / 带锚点跳转
    # ------------------------------------------------------------------
    def _toggle_help(self):
        self.help_dock.setVisible(not self.help_dock.isVisible())

    def _show_help_at(self, anchor: str = ""):
        """打开帮助面板并跳转到指定章节。"""
        self.help_dock.setVisible(True)
        if anchor and hasattr(self.page_help, "goto_anchor"):
            try:
                self.page_help.goto_anchor(anchor)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 页面跳转
    # ------------------------------------------------------------------
    def _goto(self, idx):
        self.stack.setCurrentIndex(idx)
        w = self.stack.widget(idx)
        if hasattr(w, "refresh"):
            try:
                w.refresh()
            except Exception as e:
                self.statusBar().showMessage(f"刷新失败：{e}", 5000)
        title_map = {
            PAGE_HOME: "首页",
            PAGE_SINGLE: "单笔创建",
            PAGE_BATCH: "批量导入",
            PAGE_TEMPLATES: "模板管理",
            PAGE_HISTORY: "历史记录",
        }
        self.setWindowTitle(f"订单文件夹自动创建工具 - {title_map.get(idx, '')}")
        # 根目录显示
        if self.storage.root_dir:
            self.statusBar().showMessage(f"根目录：{self.storage.root_dir}")

    def _on_root_changed(self, new_root):
        # 根目录变化，storage 已经 set 过，通知各页面刷新
        for p in (self.page_single, self.page_batch, self.page_templates, self.page_history):
            if hasattr(p, "refresh"):
                try:
                    p.refresh()
                except Exception:
                    pass
        self.statusBar().showMessage(f"根目录已切换至：{new_root}", 5000)

    def _on_salespersons_changed(self):
        """业务员列表被更新（例如扫描导入），通知相关页面刷新"""
        for p in (self.page_single, self.page_batch):
            if hasattr(p, "refresh"):
                try:
                    p.refresh()
                except Exception:
                    pass
        self.statusBar().showMessage("业务员/客户列表已更新", 5000)

    def _on_config_changed(self):
        """高级设置被保存后，通知相关页面刷新（例如产品类别下拉框）。"""
        for p in (self.page_single, self.page_batch):
            if hasattr(p, "refresh"):
                try:
                    p.refresh()
                except Exception:
                    pass
        self.statusBar().showMessage("高级设置已保存，相关页面已刷新", 5000)
