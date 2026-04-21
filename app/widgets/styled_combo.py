# -*- coding: utf-8 -*-
"""StyledComboBox —— 统一风格的自定义下拉框。

特性：
- 弹出视图用 :class:`QListView` 替换默认视图，样式由代码直接注入，
  确保即便全局 QSS 未覆盖（或被父样式干扰）时，弹出列表仍为
  Neo-brutalism 风格：白底 + 4px 粗黑边 + 0 圆角 + 鲜黄选中态。
- ``searchable=True`` 时开启模糊搜索（``Qt.MatchContains``），
  并在输入框设置 placeholder。
- 弹出宽度至少等于控件自身宽度。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QCompleter, QListView

from ..style import COLOR_BG, COLOR_INK, COLOR_SECONDARY, COLOR_WHITE


# 专供 StyledComboBox 弹出列表使用的局部 QSS，独立于全局样式。
_POPUP_QSS = f"""
QListView {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    outline: 0;
    padding: 0px;
    font-weight: bold;
}}
QListView::item {{
    padding: 6px 10px;
    min-height: 20px;
    color: {COLOR_INK};
    border: none;
    border-radius: 0px;
}}
QListView::item:hover {{
    background-color: {COLOR_BG};
    color: {COLOR_INK};
}}
QListView::item:selected {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_INK};
}}
"""


class StyledComboBox(QComboBox):
    """Neo-brutalism 风格的统一下拉框。

    参数
    ----
    searchable : bool, 默认 ``False``
        若为 ``True``，开启可编辑模糊搜索模式（``Qt.MatchContains``）。
    min_popup_width : int, 默认 ``200``
        弹出列表的最小宽度（像素）。实际弹出宽度取
        ``max(控件自身宽度, min_popup_width)``。
    parent : QWidget, 可选
        父控件。
    """

    def __init__(self, searchable: bool = False,
                 min_popup_width: int = 200, parent=None):
        super().__init__(parent)

        self._min_popup_width = int(min_popup_width)

        # 用自定义 QListView 替换默认视图，并直接注入样式，
        # 避免全局/父样式表覆盖时弹出列表看起来不一致。
        list_view = QListView(self)
        list_view.setStyleSheet(_POPUP_QSS)
        list_view.setUniformItemSizes(True)
        list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setView(list_view)

        # 控件自身尺寸策略：至少显示最长项内容
        self.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)

        if searchable:
            self._setup_searchable()

    # ------------------------------------------------------------------
    # 模糊搜索
    # ------------------------------------------------------------------
    def _setup_searchable(self):
        """启用 ``Qt.MatchContains`` 模糊搜索。"""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)

        completer = QCompleter(self.model(), self)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(completer)

        le = self.lineEdit()
        if le is not None:
            le.setPlaceholderText("输入关键字搜索…")

    # ------------------------------------------------------------------
    # 弹出宽度：至少等于控件自身宽度
    # ------------------------------------------------------------------
    def showPopup(self):
        """重写：保证弹出视图宽度 ≥ 控件宽度，且不低于 ``min_popup_width``。"""
        view = self.view()
        if view is not None:
            width = max(self.width(), self._min_popup_width)
            view.setMinimumWidth(width)
            # 同时给容器（弹出窗口）设置宽度，防止窗口本身太窄把滚动条挤出来
            container = view.parentWidget()
            if container is not None:
                container.setMinimumWidth(width)
        super().showPopup()
