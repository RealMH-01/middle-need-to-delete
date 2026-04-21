# -*- coding: utf-8 -*-
"""StyledComboBox —— 统一风格的自定义下拉框。

特性：
- 弹出视图用 :class:`QListView` 替换默认视图，样式由代码直接注入，
  确保即便全局 QSS 未覆盖（或被父样式干扰）时，弹出列表仍为
  Neo-brutalism 风格：白底 + 4px 粗黑边 + 0 圆角 + 鲜黄选中态。
- ``searchable=True`` 时开启模糊搜索（``Qt.MatchContains``），
  并在输入框设置 placeholder；同时点击输入框任意位置会自动
  弹出候选列表，避免"看起来像普通输入框"而找不到下拉功能。
- 弹出宽度至少等于控件自身宽度。
- 右侧固定贴一个 ▼ 标签覆盖在 drop-down 区域上，作为可见的
  下拉提示（纯 QSS 难以画三角，同时避免引入图片资源）。
"""

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import QComboBox, QCompleter, QLabel, QListView

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

    # drop-down 区域宽度（需要与 style.py 中 QComboBox::drop-down 的 width 保持一致）
    _DROPDOWN_WIDTH = 36

    def __init__(self, searchable: bool = False,
                 min_popup_width: int = 200, parent=None):
        super().__init__(parent)

        self._min_popup_width = int(min_popup_width)
        self._searchable = bool(searchable)

        # 用自定义 QListView 替换默认视图，并直接注入样式，
        # 避免全局/父样式表覆盖时弹出列表看起来不一致。
        list_view = QListView(self)
        list_view.setStyleSheet(_POPUP_QSS)
        list_view.setUniformItemSizes(True)
        list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setView(list_view)

        # 控件自身尺寸策略：至少显示最长项内容
        self.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)

        # ------------------------------------------------------------------
        # 可见的 ▼ 箭头：贴在右侧 drop-down 区域内。
        # 纯 QSS 的 image 属性需要外部资源，为避免引入资源文件，
        # 用 QLabel("▼") 叠加在 drop-down 上。不拦截鼠标事件，
        # 以免点击箭头时无法正常展开/收起下拉。
        # ------------------------------------------------------------------
        self._arrow_label = QLabel("▼", self)
        self._arrow_label.setAlignment(Qt.AlignCenter)
        self._arrow_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._arrow_label.setStyleSheet(
            f"QLabel {{ background: transparent; border: none; "
            f"color: {COLOR_INK}; font-weight: 900; font-size: 14px; }}"
        )

        if searchable:
            self._setup_searchable()

    # ------------------------------------------------------------------
    # 模糊搜索
    # ------------------------------------------------------------------
    def _setup_searchable(self):
        """启用 ``Qt.MatchContains`` 模糊搜索，并让点击输入框自动弹出列表。"""
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
            # 点击输入框任意位置时自动弹出候选列表。
            # 否则 editable 模式下点击只会进入文本编辑态，
            # 用户看不到"这还是一个下拉框"。
            le.installEventFilter(self)

    # ------------------------------------------------------------------
    # 事件过滤：searchable 模式下点击输入框 -> 弹出下拉
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if self._searchable and event.type() == QEvent.MouseButtonPress \
                and obj is self.lineEdit():
            view = self.view()
            if view is None or not view.isVisible():
                self.showPopup()
            # 注意：不 return True，让 QLineEdit 继续收到事件以正常放置光标
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # ▼ 箭头定位：始终贴在右侧 drop-down 区域内
    # ------------------------------------------------------------------
    def _position_arrow(self):
        if not hasattr(self, "_arrow_label") or self._arrow_label is None:
            return
        w = self._DROPDOWN_WIDTH
        h = self.height()
        x = self.width() - w
        # 让箭头占满整个 drop-down 区域，居中对齐
        self._arrow_label.setGeometry(x, 0, w, h)
        self._arrow_label.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_arrow()

    def showEvent(self, event):
        super().showEvent(event)
        self._position_arrow()

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
