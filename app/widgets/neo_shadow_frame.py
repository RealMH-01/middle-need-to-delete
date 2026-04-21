# -*- coding: utf-8 -*-
"""NeoShadowFrame —— Neo-brutalism 硬偏移阴影 QFrame 基类。

PyQt5 QSS 不支持 ``box-shadow``，对于需要高保真硬阴影的卡片容器，
本类通过重写 :meth:`paintEvent` 手绘：

    [阴影矩形]  —— 纯黑实心，向右下方偏移 shadow_offset 像素
    [本体矩形]  —— 白色填充 + 黑色边框，位于控件左上角

绘制区域按照 ``shadow_offset`` 保留 padding，确保阴影不被裁剪。
子类（后续轮次各页面的卡片容器）继承本类即可自动获得硬阴影效果。
"""

from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import QFrame

from ..style import COLOR_INK, COLOR_WHITE


class NeoShadowFrame(QFrame):
    """Neo-brutalism 风格的硬阴影 QFrame。

    参数
    ----
    shadow_offset : int, 默认 ``6``
        右下方阴影偏移量（像素）。
    shadow_color : str, 默认 :data:`~app.style.COLOR_INK`
        阴影填充颜色。默认纯黑。
    bg_color : str, 默认 :data:`~app.style.COLOR_WHITE`
        本体背景色。
    border_width : int, 默认 ``4``
        本体边框宽度（像素）。
    border_color : str, 默认 :data:`~app.style.COLOR_INK`
        本体边框颜色。
    parent : QWidget, 可选
        父控件。

    说明
    ----
    - 本类自身不设置 QSS 背景，由 :meth:`paintEvent` 全权绘制；
      因此即便全局 QSS 变动也不会让卡片"看起来怪异"。
    - 由于阴影要占位，:meth:`sizeHint` / :meth:`minimumSizeHint`
      会把 ``shadow_offset`` 计入尺寸；
      同时 :meth:`contentsMargins` 在右侧和底部预留 ``shadow_offset`` 像素，
      避免子控件被阴影覆盖。
    """

    def __init__(self, shadow_offset: int = 6,
                 shadow_color: str = COLOR_INK,
                 bg_color: str = COLOR_WHITE,
                 border_width: int = 4,
                 border_color: str = COLOR_INK,
                 parent=None):
        super().__init__(parent)
        self._shadow_offset = int(shadow_offset)
        self._shadow_color = QColor(shadow_color)
        self._bg_color = QColor(bg_color)
        self._border_width = int(border_width)
        self._border_color = QColor(border_color)

        # 清空 QFrame 默认 frame 绘制，阴影/边框都由 paintEvent 负责
        self.setFrameShape(QFrame.NoFrame)
        # 关键：告诉 Qt 本控件不透明，背景自行绘制
        self.setAttribute(Qt.WA_StyledBackground, False)

        # 给子控件留出右 / 下侧的阴影空间
        self.setContentsMargins(
            self._border_width,
            self._border_width,
            self._border_width + self._shadow_offset,
            self._border_width + self._shadow_offset,
        )

    # ------------------------------------------------------------------
    # 动态调整参数
    # ------------------------------------------------------------------
    def set_shadow_offset(self, offset: int):
        """运行时修改阴影偏移量并刷新 contents margin。"""
        self._shadow_offset = int(offset)
        self.setContentsMargins(
            self._border_width,
            self._border_width,
            self._border_width + self._shadow_offset,
            self._border_width + self._shadow_offset,
        )
        self.updateGeometry()
        self.update()

    # ------------------------------------------------------------------
    # 尺寸提示：把阴影计入
    # ------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        return QSize(
            hint.width() + self._shadow_offset,
            hint.height() + self._shadow_offset,
        )

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        return QSize(
            hint.width() + self._shadow_offset,
            hint.height() + self._shadow_offset,
        )

    # ------------------------------------------------------------------
    # 绘制：先画阴影，再画本体
    # ------------------------------------------------------------------
    def paintEvent(self, event):  # noqa: N802  (Qt 命名约定)
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing, False)

            w = self.width()
            h = self.height()
            offset = self._shadow_offset

            # ---- 1. 阴影矩形：向右下方偏移 offset 像素 ----
            if offset > 0:
                shadow_rect = QRect(
                    offset, offset,
                    max(0, w - offset),
                    max(0, h - offset),
                )
                painter.fillRect(shadow_rect, QBrush(self._shadow_color))

            # ---- 2. 本体矩形：左上角对齐，整体比控件小 offset ----
            body_rect = QRect(0, 0, max(0, w - offset), max(0, h - offset))
            painter.fillRect(body_rect, QBrush(self._bg_color))

            # ---- 3. 本体边框 ----
            if self._border_width > 0 and body_rect.width() > 0 \
                    and body_rect.height() > 0:
                pen = QPen(self._border_color)
                pen.setWidth(self._border_width)
                pen.setJoinStyle(Qt.MiterJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                # QRect 的 drawRect 描边从矩形的中心线向外扩，
                # 为了让边框完全包在 body_rect 内，内缩 border_width/2
                inset = self._border_width // 2
                stroke_rect = body_rect.adjusted(
                    inset, inset,
                    -inset - (self._border_width % 2),
                    -inset - (self._border_width % 2),
                )
                painter.drawRect(stroke_rect)
        finally:
            painter.end()

        # 不调用父类 paintEvent —— 背景已完全由我们绘制。
        # （如需显示子控件，Qt 会在本方法返回后继续派发子控件的 paintEvent。）
