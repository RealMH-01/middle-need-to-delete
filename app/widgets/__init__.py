# -*- coding: utf-8 -*-
"""自定义控件

本包集中存放 Neo-brutalism 风格的公共控件，供各页面 / 对话框复用：

- :class:`StyledComboBox`：带 Neo-brutalism 风格弹出列表的下拉框，
  支持模糊搜索（``searchable=True``）。
- :class:`NeoShadowFrame`：带硬偏移阴影的 QFrame 基类，
  用 paintEvent 手绘右下方向的纯黑阴影，可作为各页面卡片容器的基类。
"""

from .styled_combo import StyledComboBox
from .neo_shadow_frame import NeoShadowFrame

__all__ = ["StyledComboBox", "NeoShadowFrame"]
