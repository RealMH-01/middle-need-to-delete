# -*- coding: utf-8 -*-
"""全局样式表（QSS）—— Neo-brutalism（新野兽风格）。

设计语言要点：
- 奶油色纸感背景 + 纯黑墨色（文字 / 边框 / 阴影），绝不使用任何灰色。
- 4px 纯黑边框是全局标志性特征，几乎所有可见元素都有。
- 0 圆角（直角），仅徽章 / 标签可做药丸形。
- 高饱和度配色：热红 #FF6B6B、鲜黄 #FFD93D、柔紫 #C4B5FD。
- 粗重字体（Bold / Black），聚焦态背景变黄以形成强视觉反馈。
- 阴影：QSS 无 box-shadow，使用不等宽边框 + paintEvent 两种方式模拟右下硬阴影。

对外导出常量：
    - 颜色 Token：``COLOR_BG`` / ``COLOR_INK`` / ``COLOR_ACCENT`` /
      ``COLOR_SECONDARY`` / ``COLOR_MUTED`` / ``COLOR_WHITE``
    - 字体常量：``FONT_FAMILY`` / ``FONT_BODY_SIZE`` / ``FONT_TITLE_SIZE`` …
    - ``APP_QSS``：可直接 ``app.setStyleSheet(APP_QSS)``
"""

# =====================================================================
# 颜色 Token（Neo-brutalism 核心色板 —— 禁止任何灰色）
# =====================================================================
COLOR_BG = "#FFFDF5"          # 主背景 / 画布：奶油色，纸张质感
COLOR_INK = "#000000"         # 前景 / 墨色：纯黑（文字、边框、阴影）
COLOR_ACCENT = "#FF6B6B"      # 强调色：热红（主按钮、重要操作）
COLOR_ACCENT_HOVER = "#FF5252"  # 强调色 hover 加深
COLOR_SECONDARY = "#FFD93D"   # 次要色：鲜黄（次要按钮、徽章、聚焦态）
COLOR_MUTED = "#C4B5FD"       # 柔和色：柔紫（卡片头部、表头、装饰）
COLOR_WHITE = "#FFFFFF"       # 白：输入框 / 面板背景、深底上的文字

# ---------------------------------------------------------------------
# 向后兼容别名（保留老代码可能使用的名字，全部指向 Neo-brutalism 色板）
# 注意：没有灰色 —— 原先的灰色语义统一替换为纯黑。
# ---------------------------------------------------------------------
COLOR_SURFACE = COLOR_WHITE              # 面板 / 卡片背景
COLOR_BORDER = COLOR_INK                 # 默认边框（纯黑）
COLOR_BORDER_HOVER = COLOR_INK           # hover 边框同样为纯黑
COLOR_TEXT = COLOR_INK                   # 主文字：纯黑
COLOR_TEXT_SUB = COLOR_INK               # 次级文字也是纯黑（禁止灰色）
COLOR_PRIMARY = COLOR_ACCENT             # 主色 = 热红
COLOR_PRIMARY_HOVER = COLOR_ACCENT_HOVER
COLOR_PRIMARY_PRESSED = COLOR_ACCENT_HOVER
COLOR_PRIMARY_LIGHT = COLOR_SECONDARY    # 选中态背景 = 鲜黄
COLOR_PRIMARY_DARK = COLOR_ACCENT_HOVER
COLOR_DANGER = COLOR_ACCENT
COLOR_DANGER_BG = COLOR_ACCENT
COLOR_SUCCESS = COLOR_ACCENT
COLOR_BLUE = COLOR_ACCENT
COLOR_GREEN = COLOR_ACCENT
COLOR_GRAY = COLOR_INK


# =====================================================================
# 字体（Space Grotesk 优先，中文回退 Microsoft YaHei UI）
# =====================================================================
FONT_FAMILY = ('"Space Grotesk", "Microsoft YaHei UI", "Microsoft YaHei", '
               '"微软雅黑", "PingFang SC", "Segoe UI", sans-serif')
FONT_BODY_SIZE = "14px"
FONT_TITLE_SIZE = "16px"
FONT_BUTTON_SIZE = "14px"
FONT_HINT_SIZE = "13px"


# =====================================================================
# Neo-brutalism QSS
# =====================================================================
APP_QSS = f"""
/* ==================== 全局 ==================== */
* {{
    font-family: {FONT_FAMILY};
    font-size: {FONT_BODY_SIZE};
    font-weight: bold;
    color: {COLOR_INK};
}}

QMainWindow, QWidget {{
    background-color: {COLOR_BG};
}}

QDialog {{
    background-color: {COLOR_BG};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
}}

/* ==================== Labels ==================== */
QLabel {{
    background: transparent;
    color: {COLOR_INK};
    font-weight: bold;
}}

QLabel#TitleLabel {{
    font-size: 24px;
    font-weight: 900;
    color: {COLOR_INK};
    padding: 8px 0;
    letter-spacing: 0.5px;
}}

QLabel#SubTitleLabel {{
    font-size: 16px;
    font-weight: bold;
    color: {COLOR_INK};
    padding: 2px 0;
}}

QLabel#SectionLabel {{
    font-size: {FONT_TITLE_SIZE};
    font-weight: 900;
    color: {COLOR_INK};
    padding: 2px 0;
}}

QLabel#HintLabel {{
    font-size: {FONT_HINT_SIZE};
    font-weight: bold;
    color: {COLOR_INK};
}}

/* ==================== 按钮 ==================== */
/* 主按钮：热红底 + 粗黑边 + 右下硬阴影（用不等宽边框模拟）*/
QPushButton {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_INK};
    border-top: 4px solid {COLOR_INK};
    border-left: 4px solid {COLOR_INK};
    border-right: 7px solid {COLOR_INK};
    border-bottom: 7px solid {COLOR_INK};
    border-radius: 0px;
    padding: 8px 20px;
    min-height: 24px;
    font-size: {FONT_BUTTON_SIZE};
    font-weight: 900;
    text-transform: uppercase;
}}
QPushButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}
/* 按下：四边边框统一为 4px，同时位移 3px 模拟"被压扁"的机械感 */
QPushButton:pressed {{
    background-color: {COLOR_ACCENT_HOVER};
    border: 4px solid {COLOR_INK};
    margin-left: 3px;
    margin-top: 3px;
    margin-right: 0px;
    margin-bottom: 0px;
}}
QPushButton:disabled {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_INK};
    border-top: 4px solid {COLOR_INK};
    border-left: 4px solid {COLOR_INK};
    border-right: 7px solid {COLOR_INK};
    border-bottom: 7px solid {COLOR_INK};
}}

/* 次要按钮：白底 + 粗黑边 + 硬阴影 */
QPushButton#SecondaryButton {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border-top: 4px solid {COLOR_INK};
    border-left: 4px solid {COLOR_INK};
    border-right: 7px solid {COLOR_INK};
    border-bottom: 7px solid {COLOR_INK};
}}
QPushButton#SecondaryButton:hover {{
    background-color: {COLOR_SECONDARY};
}}
QPushButton#SecondaryButton:pressed {{
    background-color: {COLOR_SECONDARY};
    border: 4px solid {COLOR_INK};
    margin-left: 3px;
    margin-top: 3px;
    margin-right: 0px;
    margin-bottom: 0px;
}}
QPushButton#SecondaryButton:disabled {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
}}

/* 危险按钮：白底红字 + 粗黑边；hover 转为红底白字 */
QPushButton#DangerButton {{
    background-color: {COLOR_WHITE};
    color: {COLOR_ACCENT};
    border-top: 4px solid {COLOR_INK};
    border-left: 4px solid {COLOR_INK};
    border-right: 7px solid {COLOR_INK};
    border-bottom: 7px solid {COLOR_INK};
}}
QPushButton#DangerButton:hover {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_WHITE};
}}
QPushButton#DangerButton:pressed {{
    background-color: {COLOR_ACCENT_HOVER};
    color: {COLOR_WHITE};
    border: 4px solid {COLOR_INK};
    margin-left: 3px;
    margin-top: 3px;
    margin-right: 0px;
    margin-bottom: 0px;
}}

/* 大按钮（首页英雄入口）：黄底 + 8px 粗黑边 + 更深的右下硬阴影 */
QPushButton#BigButton {{
    font-size: 20px;
    font-weight: 900;
    padding: 30px 50px;
    min-width: 200px;
    min-height: 100px;
    background-color: {COLOR_SECONDARY};
    color: {COLOR_INK};
    border-top: 8px solid {COLOR_INK};
    border-left: 8px solid {COLOR_INK};
    border-right: 12px solid {COLOR_INK};
    border-bottom: 12px solid {COLOR_INK};
    border-radius: 0px;
    text-transform: uppercase;
}}
QPushButton#BigButton:hover {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_WHITE};
}}
QPushButton#BigButton:pressed {{
    border: 8px solid {COLOR_INK};
    margin-left: 4px;
    margin-top: 4px;
    margin-right: 0px;
    margin-bottom: 0px;
}}

/* 链接按钮：透明 + 下划线 + 无边框；hover 变黄底 */
QPushButton#LinkButton {{
    background-color: transparent;
    color: {COLOR_INK};
    border: none;
    padding: 4px 8px;
    text-decoration: underline;
    font-weight: bold;
    text-transform: none;
}}
QPushButton#LinkButton:hover {{
    background-color: {COLOR_SECONDARY};
}}
QPushButton#LinkButton:pressed {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_WHITE};
    margin: 0;
}}

/* ==================== 输入框 ==================== */
/* 白底 + 4px 粗黑边 + 0 圆角；:focus 背景变鲜黄（Neo-brutalism 标志）*/
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    padding: 6px 10px;
    min-height: 22px;
    font-weight: bold;
    selection-background-color: {COLOR_SECONDARY};
    selection-color: {COLOR_INK};
}}
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover,
QSpinBox:hover, QDoubleSpinBox:hover {{
    background-color: {COLOR_WHITE};
    border: 4px solid {COLOR_INK};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{
    background-color: {COLOR_SECONDARY};
    border: 4px solid {COLOR_INK};
    color: {COLOR_INK};
}}
QLineEdit:disabled, QTextEdit:disabled,
QPlainTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    background-color: {COLOR_BG};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
}}

/* ==================== ComboBox ==================== */
QComboBox {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    padding: 6px 10px;
    min-height: 22px;
    font-weight: bold;
    selection-background-color: {COLOR_SECONDARY};
    selection-color: {COLOR_INK};
}}
QComboBox:hover {{
    background-color: {COLOR_WHITE};
}}
QComboBox:focus {{
    background-color: {COLOR_SECONDARY};
    border: 4px solid {COLOR_INK};
}}
QComboBox:disabled {{
    background-color: {COLOR_BG};
    color: {COLOR_INK};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
    subcontrol-origin: padding;
    subcontrol-position: top right;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    selection-background-color: {COLOR_SECONDARY};
    selection-color: {COLOR_INK};
    padding: 0px;
    outline: 0;
    font-weight: bold;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    min-height: 20px;
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_INK};
}}

/* ==================== CheckBox / RadioButton ==================== */
QCheckBox, QRadioButton {{
    spacing: 8px;
    background: transparent;
    color: {COLOR_INK};
    font-weight: bold;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 3px solid {COLOR_INK};
    background-color: {COLOR_WHITE};
    border-radius: 0px;
}}
QRadioButton::indicator {{
    border-radius: 9px;
}}
QCheckBox::indicator:checked {{
    background-color: {COLOR_ACCENT};
}}
QRadioButton::indicator:checked {{
    background-color: {COLOR_ACCENT};
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    background-color: {COLOR_SECONDARY};
}}

/* ==================== 表格 ==================== */
QTableWidget, QTableView {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    gridline-color: {COLOR_INK};
    selection-background-color: {COLOR_SECONDARY};
    selection-color: {COLOR_INK};
    alternate-background-color: {COLOR_BG};
    font-weight: bold;
}}
QTableWidget::item, QTableView::item {{
    padding: 6px 4px;
    color: {COLOR_INK};
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_INK};
}}

QHeaderView::section {{
    background-color: {COLOR_MUTED};
    color: {COLOR_INK};
    padding: 8px 6px;
    border: none;
    border-right: 2px solid {COLOR_INK};
    border-bottom: 4px solid {COLOR_INK};
    font-weight: 900;
}}
QHeaderView::section:last {{
    border-right: none;
}}
QTableCornerButton::section {{
    background-color: {COLOR_MUTED};
    border: none;
    border-right: 2px solid {COLOR_INK};
    border-bottom: 4px solid {COLOR_INK};
}}

/* ==================== 树 ==================== */
QTreeWidget, QTreeView {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    padding: 4px;
    selection-background-color: {COLOR_SECONDARY};
    selection-color: {COLOR_INK};
    outline: 0;
    font-weight: bold;
}}
QTreeWidget::item, QTreeView::item {{
    padding: 4px 2px;
    border-radius: 0px;
    color: {COLOR_INK};
}}
QTreeWidget::item:hover, QTreeView::item:hover {{
    background-color: {COLOR_BG};
}}
QTreeWidget::item:selected, QTreeView::item:selected {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_INK};
}}

/* ==================== 列表 ==================== */
QListWidget, QListView {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    padding: 4px;
    selection-background-color: {COLOR_SECONDARY};
    selection-color: {COLOR_INK};
    outline: 0;
    font-weight: bold;
}}
QListWidget::item, QListView::item {{
    padding: 6px 10px;
    border-radius: 0px;
    color: {COLOR_INK};
}}
QListWidget::item:hover, QListView::item:hover {{
    background-color: {COLOR_BG};
}}
QListWidget::item:selected, QListView::item:selected {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_INK};
}}

/* ==================== GroupBox ==================== */
QGroupBox {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    margin-top: 16px;
    padding: 16px 10px 10px 10px;
    font-weight: 900;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {COLOR_INK};
    font-size: {FONT_TITLE_SIZE};
    font-weight: 900;
    background-color: {COLOR_BG};
}}

/* ==================== TabWidget ==================== */
QTabWidget::pane {{
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    background-color: {COLOR_WHITE};
    top: -1px;
}}
QTabBar::tab {{
    background: {COLOR_WHITE};
    color: {COLOR_INK};
    padding: 8px 18px;
    border: 2px solid {COLOR_INK};
    border-radius: 0px;
    margin-right: 2px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    background: {COLOR_SECONDARY};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
    border-bottom: none;
    font-weight: 900;
}}
QTabBar::tab:hover:!selected {{
    background: {COLOR_BG};
}}

/* ==================== Menu ==================== */
QMenu {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    padding: 4px;
    font-weight: bold;
}}
QMenu::item {{
    padding: 6px 18px;
    border-radius: 0px;
    color: {COLOR_INK};
}}
QMenu::item:selected {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_INK};
}}
QMenu::separator {{
    height: 2px;
    background: {COLOR_INK};
    margin: 4px 8px;
}}

QMenuBar {{
    background-color: {COLOR_WHITE};
    color: {COLOR_INK};
    border-bottom: 4px solid {COLOR_INK};
    font-weight: bold;
}}
QMenuBar::item {{
    padding: 6px 12px;
    background: transparent;
    border-radius: 0px;
    color: {COLOR_INK};
}}
QMenuBar::item:selected {{
    background-color: {COLOR_SECONDARY};
}}

/* ==================== ToolTip ==================== */
/* 连 tooltip 也要有黑边 —— 这就是 Neo-brutalism */
QToolTip {{
    background-color: {COLOR_INK};
    color: {COLOR_WHITE};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    padding: 6px 10px;
    font-size: {FONT_HINT_SIZE};
    font-weight: bold;
}}

/* ==================== ScrollBar ==================== */
QScrollBar:vertical {{
    background: {COLOR_BG};
    width: 12px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_INK};
    border: none;
    border-radius: 0px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: transparent;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: {COLOR_BG};
    height: 12px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {COLOR_INK};
    border: none;
    border-radius: 0px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLOR_ACCENT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: transparent;
}}

/* ==================== StatusBar ==================== */
QStatusBar {{
    background-color: {COLOR_WHITE};
    border-top: 4px solid {COLOR_INK};
    color: {COLOR_INK};
    font-weight: bold;
}}
QStatusBar::item {{
    border: none;
}}

/* ==================== Dialog Button Box ==================== */
QDialogButtonBox QPushButton {{
    min-width: 80px;
}}

/* ==================== ProgressBar ==================== */
QProgressBar {{
    background-color: {COLOR_WHITE};
    border: 4px solid {COLOR_INK};
    border-radius: 0px;
    text-align: center;
    color: {COLOR_INK};
    font-weight: 900;
}}
QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
}}

/* ==================== Splitter ==================== */
QSplitter::handle {{
    background-color: {COLOR_INK};
}}
QSplitter::handle:horizontal {{
    width: 4px;
}}
QSplitter::handle:vertical {{
    height: 4px;
}}
"""
