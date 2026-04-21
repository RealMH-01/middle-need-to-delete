# -*- coding: utf-8 -*-
"""订单文件夹自动创建工具 - 程序入口。"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication

from app.main_window import MainWindow
from app.style import APP_QSS


def _pick_font_family() -> str:
    """选择全局字体族。

    Neo-brutalism 首选 Space Grotesk（若系统已安装），
    否则回退到 Microsoft YaHei UI → Microsoft YaHei（Windows 中文标配）。
    桌面工具不强制要求用户安装字体，因此 Space Grotesk 仅作可选增强。
    """
    families = set(QFontDatabase().families())
    for candidate in ("Space Grotesk", "Microsoft YaHei UI",
                      "Microsoft YaHei"):
        if candidate in families:
            return candidate
    # 最后兜底：用 Microsoft YaHei 作为字符串（即便系统没有，
    # Qt 也会按其 font-family 回退机制使用默认中文字体）
    return "Microsoft YaHei"


def main():
    """启动应用。"""
    # 高 DPI 适配（必须在 QApplication 构造前设置）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("订单文件夹自动创建工具")

    # 底层样式引擎使用 Fusion，跨平台观感最一致
    try:
        app.setStyle("Fusion")
    except Exception:
        pass

    # 全局字体：Neo-brutalism 粗重字体（700 / Bold），字号 11
    family = _pick_font_family()
    font = QFont(family, 11)
    font.setWeight(QFont.Bold)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    # 全局样式表（Neo-brutalism QSS）
    app.setStyleSheet(APP_QSS)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
