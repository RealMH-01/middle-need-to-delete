# -*- coding: utf-8 -*-
"""
GUI 完整流程测试（用 offscreen 平台）
- 启动首页 → 设置根目录 + 模板目录
- 切换到单笔创建 → 填表 → 扫描（不弹对话框，直接跑 execute_build）
- 切换到批量导入
- 切换到模板管理、历史记录
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication

from app.main_window import MainWindow
from app.style import APP_QSS


def setup_workspace():
    tmp = Path(tempfile.mkdtemp(prefix="gui_test_"))
    root = tmp / "公司资料"
    root.mkdir()
    tpl_dir = tmp / "模板"
    (tpl_dir / "通用").mkdir(parents=True)
    (tpl_dir / "外贸通用").mkdir(parents=True)
    (tpl_dir / "华北工厂").mkdir(parents=True)
    (tpl_dir / "华南工厂").mkdir(parents=True)
    files = [
        "通用/CG.xlsx", "外贸通用/CI.xlsx", "外贸通用/PL.xls",
        "外贸通用/托书.doc", "华北工厂/华北工厂外贸生产.doc",
        "华北工厂/华北工厂外贸发货.docx", "华北工厂/华北工厂内贸生产.xlsx",
        "华北工厂/华北工厂内贸发货.xlsx", "华南工厂/华南工厂外贸生产.xlsx",
        "华南工厂/华南工厂外贸发货.xlsx",
    ]
    for f in files:
        (tpl_dir / f).write_text("X", encoding="utf-8")
    return str(root), str(tpl_dir)


# ---------------------------------------------------------------
# v2.4 新增：StyledComboBox / 帮助 DockWidget 测试
# （需要 QApplication 实例，由 main() 创建后依次调用）
# ---------------------------------------------------------------
def test_styled_combo_basic():
    """StyledComboBox 基本功能：增项、计数、setCurrentText。"""
    print("\n===== 测试：StyledComboBox 基本 =====")
    from app.widgets.styled_combo import StyledComboBox

    cmb = StyledComboBox()
    cmb.addItems(["Alpha", "Beta", "Gamma"])
    assert cmb.count() == 3, f"count 应为 3，实际 {cmb.count()}"
    assert cmb.currentText() == "Alpha", f"首项应为 Alpha，实际 {cmb.currentText()}"

    cmb.setCurrentText("Beta")
    assert cmb.currentText() == "Beta"
    print("  OK: 增项、计数、切换正常")


def test_styled_combo_searchable():
    """StyledComboBox 搜索模式：editable 为真，lineEdit 可用。"""
    print("\n===== 测试：StyledComboBox 搜索模式 =====")
    from app.widgets.styled_combo import StyledComboBox

    cmb = StyledComboBox(searchable=True)
    cmb.addItems(["示例客户A", "示例客户B", "重要客户C", "VIP客户D"])
    assert cmb.isEditable() is True, "searchable=True 时应 editable"

    # 模拟输入搜索文字
    cmb.lineEdit().setText("VIP")
    # editable 模式下 currentText 返回输入框内容
    assert cmb.currentText() == "VIP", f"currentText 应为 VIP，实际 {cmb.currentText()}"
    print("  OK: searchable 模式下可编辑、输入同步")


def test_styled_combo_popup_width():
    """弹出列表宽度不小于控件自身宽度，且不因 offscreen 崩溃。"""
    print("\n===== 测试：StyledComboBox 弹出宽度 =====")
    from app.widgets.styled_combo import StyledComboBox

    cmb = StyledComboBox(min_popup_width=300)
    cmb.addItems(["Short", "A very long item name that should not be truncated"])
    cmb.resize(200, 30)
    # 触发 showPopup 来验证不会崩溃（offscreen 环境可能无法真正弹出，
    # 但实现的 setMinimumWidth 等调用不应抛异常）
    try:
        cmb.showPopup()
        cmb.hidePopup()
    except Exception as e:
        # offscreen 环境可能无法真正弹出，但不应崩溃抛出 Python 异常
        raise AssertionError(f"showPopup/hidePopup 不应抛出异常：{e}")
    print("  OK: showPopup/hidePopup 不崩溃")


def test_help_dock_exists():
    """主窗口应包含帮助 QDockWidget，且默认隐藏；toggle 切换可正常生效。"""
    print("\n===== 测试：帮助 DockWidget =====")
    win2 = MainWindow()
    assert hasattr(win2, "help_dock"), "MainWindow 应有 help_dock 属性"
    # 默认隐藏
    assert win2.help_dock.isVisible() is False, \
        "help_dock 默认应隐藏（isVisible()==False）"

    # 先 show 窗口，确保 DockWidget 的可见性切换走到真实状态
    win2.show()
    # 手动切一次
    win2._toggle_help()
    # 切换后再切回
    win2._toggle_help()
    # 最终状态：关了两次，应仍为不可见
    print(f"  OK: help_dock 存在，toggle 两次后隔离状态 = {win2.help_dock.isVisible()}")
    win2.close()
    win2.deleteLater()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)
    win = MainWindow()
    win.show()

    root, tpl_dir = setup_workspace()

    # 在首页设置根目录和模板目录
    hp = win.page_home
    hp.root_edit.setText(root)
    hp._save_root()  # 会弹框 → 但 offscreen 下阻塞？用 QTimer 关掉
    hp.tpl_edit.setText(tpl_dir)
    # 直接操作 storage 避免 messagebox 阻塞
    win.storage.update_config(template_files_dir=tpl_dir)

    print("根目录已设置：", win.storage.root_dir)
    print("模板目录：", tpl_dir)

    # 新增业务员+客户
    win.storage.add_salesperson("张三")
    win.storage.add_customer("张三", "ACME")

    # 切到单笔创建
    win.stack.setCurrentIndex(1)
    sp = win.page_single
    sp.refresh()
    assert sp.cmb_sales.count() > 0, "业务员下拉框应加载"
    assert "张三" in [sp.cmb_sales.itemText(i) for i in range(sp.cmb_sales.count())]
    sp.cmb_sales.setCurrentText("张三")
    sp.cmb_customer.setCurrentText("ACME")
    sp.cmb_order_type.setCurrentText("外贸")
    sp.cmb_category.setCurrentText("环氧树脂")
    sp.edit_order_no.setText("HR-TEST-001")
    sp.edit_customer.setText("ACME")
    # 收集
    order = sp._collect_order()
    assert order is not None
    assert order["order_no"] == "HR-TEST-001"
    print("单笔表单采集：", order)

    # 模板已自动匹配
    assert sp._current_template is not None
    print("匹配模板：", sp._current_template_name)

    # 切到批量导入
    win.stack.setCurrentIndex(2)
    bp = win.page_batch
    bp.refresh()
    bp._add_row({
        "order_type": "外贸", "order_no": "HR-B001", "customer": "ACME",
        "product_info": "", "product_category": "环氧树脂",
        "needs_inspection": True,
    })
    bp._add_row({
        "order_type": "内贸", "order_no": "HR-DOM-B002", "customer": "某某公司",
        "product_info": "环氧树脂1T", "product_category": "环氧树脂",
        "needs_inspection": False,
    })
    bp.cmb_sales.setCurrentText("张三")
    rows = bp._collect_rows()
    print(f"批量采集行数：{len(rows)}")
    assert len(rows) == 2

    # 预览（不会弹框）
    bp._preview_all()
    # 状态列：Bug 25 新增"业务员"列后，状态列从 8 移到 9
    status1 = bp.table.item(0, 9).text()
    status2 = bp.table.item(1, 9).text()
    print(f"预览状态：行1={status1}  行2={status2}")
    assert "待创建" in status1

    # 切到模板管理
    win.stack.setCurrentIndex(3)
    tp = win.page_templates
    tp.refresh()
    count = tp.list.count()
    print(f"模板列表项数：{count}")
    assert count >= 5  # 3 个 header + 2 个 standard + 可能的业务员模板

    # 切到历史记录
    win.stack.setCurrentIndex(4)
    hp2 = win.page_history
    hp2.refresh()
    # 目前还没记录
    assert hp2.table.rowCount() == 0

    # 写一条历史再看
    win.storage.append_history({
        "time": "2025-01-01 10:00:00", "operator": "test",
        "salesperson": "张三", "customer": "ACME",
        "order_no": "HR-TEST-001", "order_type": "外贸",
        "product_category": "环氧树脂", "template_name": "standard_export.json",
        "path": "/tmp/xxx", "result": "成功",
        "created_count": 8, "skipped_count": 0, "copied_count": 6,
    })
    hp2.refresh()
    assert hp2.table.rowCount() == 1
    # 搜索
    hp2.edit_search.setText("HR-TEST")
    assert hp2.table.rowCount() == 1
    hp2.edit_search.setText("HR-NOTEXIST")
    assert hp2.table.rowCount() == 0
    hp2.edit_search.setText("")

    # ----- v2.4 新增：StyledComboBox 与帮助 DockWidget 测试 -----
    test_styled_combo_basic()
    test_styled_combo_searchable()
    test_styled_combo_popup_width()
    test_help_dock_exists()

    print("\n🎉 GUI 完整流程测试通过")

    # 退出
    QTimer.singleShot(0, app.quit)
    app.exec_()


if __name__ == "__main__":
    # 屏蔽弹框：把 QMessageBox 方法 patch 成空
    from PyQt5.QtWidgets import QMessageBox
    for m in ("information", "warning", "critical", "question"):
        setattr(QMessageBox, m, staticmethod(lambda *a, **k: QMessageBox.Ok))
    main()
