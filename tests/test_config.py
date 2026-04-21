# -*- coding: utf-8 -*-
"""配置外移相关的 pytest 风格测试。

覆盖以下场景：
- resolve_file_template / resolve_filename_with_ext 接收外部传入的
  origin_map 和 origin_file_ext 参数后能正确解析；
- origin_map 为空或缺少当前产品类别时不崩溃，返回 None；
- order_root_folder 从 config 读取正确，缺失时回退默认值 "1订单"；
- _is_mid_layer_name 从 config 读取关键词列表；关键词列表为空时始终返回 False；
- build_customer_dir 在新的 property 机制下路径拼接正确；
- set_root_dir 对旧版 config.json（缺少新字段）能自动补写默认值。
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# 让测试可以 import app.*
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest

from app.core import folder_builder
from app.core.storage import (
    DEFAULT_MID_LAYER_KEYWORDS,
    DEFAULT_ORDER_ROOT_FOLDER,
    DEFAULT_ORIGIN_FILE_EXT,
    DEFAULT_ORIGIN_MAP,
    Storage,
)


# ---------------------------------------------------------------
# 测试辅助
# ---------------------------------------------------------------
@pytest.fixture
def tmp_root(tmp_path):
    """提供一个已初始化的 Storage 实例。"""
    root = tmp_path / "公司资料"
    root.mkdir()
    return root


@pytest.fixture
def storage(tmp_root):
    return Storage(str(tmp_root))


# ---------------------------------------------------------------
# resolve_file_template / resolve_filename_with_ext
# ---------------------------------------------------------------
class TestResolveFileTemplate:
    def test_basic_resolution(self):
        """外部传入 origin_map / origin_file_ext 能正确解析。"""
        om = {"A类": "A工厂", "B类": "B工厂"}
        oe = {
            "A工厂/外贸生产": ".doc",
            "A工厂/外贸发货": ".docx",
            "B工厂/外贸生产": ".xlsx",
        }
        # 产品类别=A类 → A工厂
        r = folder_builder.resolve_file_template(
            "[产地]外贸生产", "A类", om, oe)
        assert r == "A工厂/A工厂外贸生产.doc"

        # 产品类别=B类 → B工厂
        r = folder_builder.resolve_file_template(
            "[产地]外贸生产", "B类", om, oe)
        assert r == "B工厂/B工厂外贸生产.xlsx"

    def test_default_mapping_still_works(self):
        """默认映射：环氧树脂 → 华北工厂."""
        r = folder_builder.resolve_file_template(
            "[产地]外贸生产", "环氧树脂",
            DEFAULT_ORIGIN_MAP, DEFAULT_ORIGIN_FILE_EXT)
        assert r == "华北工厂/华北工厂外贸生产.doc"

        r = folder_builder.resolve_file_template(
            "[产地]外贸发货", "其他产品",
            DEFAULT_ORIGIN_MAP, DEFAULT_ORIGIN_FILE_EXT)
        assert r == "华南工厂/华南工厂外贸发货.xlsx"

    def test_empty_origin_map_returns_none(self):
        """origin_map 为空时不应崩溃，应返回 None。"""
        r = folder_builder.resolve_file_template(
            "[产地]外贸生产", "环氧树脂", {}, DEFAULT_ORIGIN_FILE_EXT)
        assert r is None

        # None 也可接受
        r = folder_builder.resolve_file_template(
            "[产地]外贸生产", "环氧树脂", None, DEFAULT_ORIGIN_FILE_EXT)
        assert r is None

    def test_missing_category_returns_none(self):
        """origin_map 不含当前产品类别时应返回 None。"""
        om = {"A类": "A工厂"}
        oe = {"A工厂/外贸生产": ".doc"}
        r = folder_builder.resolve_file_template(
            "[产地]外贸生产", "未知类别", om, oe)
        assert r is None

    def test_missing_extension_returns_none(self):
        """产地存在但扩展名配置缺失时返回 None。"""
        om = {"A类": "A工厂"}
        oe = {}  # 扩展名配置空
        r = folder_builder.resolve_file_template(
            "[产地]外贸生产", "A类", om, oe)
        assert r is None

    def test_no_placeholder_returns_as_is(self):
        """没有 [产地] 标记时，原样返回。"""
        r = folder_builder.resolve_file_template(
            "通用/CG.xlsx", "环氧树脂",
            DEFAULT_ORIGIN_MAP, DEFAULT_ORIGIN_FILE_EXT)
        assert r == "通用/CG.xlsx"

    def test_none_or_empty_tmpl(self):
        """tmpl 为 None 或空串时，原样返回。"""
        assert folder_builder.resolve_file_template(
            None, "环氧树脂", DEFAULT_ORIGIN_MAP, DEFAULT_ORIGIN_FILE_EXT) is None
        assert folder_builder.resolve_file_template(
            "", "环氧树脂", DEFAULT_ORIGIN_MAP, DEFAULT_ORIGIN_FILE_EXT) == ""


class TestResolveFilenameWithExt:
    def test_appends_ext_from_template(self):
        """filename 没有后缀时，从模板解析出扩展名。"""
        r = folder_builder.resolve_filename_with_ext(
            "生产通知单-ORD001", "[产地]外贸生产", "环氧树脂",
            DEFAULT_ORIGIN_MAP, DEFAULT_ORIGIN_FILE_EXT)
        assert r == "生产通知单-ORD001.doc"

    def test_keeps_existing_ext(self):
        """filename 已有后缀时，不改动。"""
        r = folder_builder.resolve_filename_with_ext(
            "CI-ORD001.xlsx", "通用/CI.xlsx", "环氧树脂",
            DEFAULT_ORIGIN_MAP, DEFAULT_ORIGIN_FILE_EXT)
        assert r == "CI-ORD001.xlsx"

    def test_no_template_no_ext(self):
        """没有模板也没有后缀时，原样返回。"""
        r = folder_builder.resolve_filename_with_ext(
            "注意事项", None, "环氧树脂",
            DEFAULT_ORIGIN_MAP, DEFAULT_ORIGIN_FILE_EXT)
        assert r == "注意事项"


# ---------------------------------------------------------------
# Storage: order_root_folder property
# ---------------------------------------------------------------
class TestOrderRootFolder:
    def test_default_value_after_init(self, storage):
        """首次 set_root_dir 后，order_root_folder 应为默认值。"""
        assert storage.order_root_folder == DEFAULT_ORDER_ROOT_FOLDER
        assert storage.order_root_folder == "1订单"

    def test_custom_value_via_config(self, storage):
        """config 中自定义后应生效。"""
        storage.update_config(order_root_folder="Orders")
        assert storage.order_root_folder == "Orders"

    def test_fallback_when_missing(self, storage):
        """config 中没有该字段时回退到默认值。"""
        cfg = storage.load_config()
        cfg.pop("order_root_folder", None)
        storage.save_config(cfg)
        assert storage.order_root_folder == DEFAULT_ORDER_ROOT_FOLDER

    def test_build_customer_dir_uses_custom(self, storage):
        """build_customer_dir 应按 config 里的 order_root_folder 拼接。"""
        storage.update_config(order_root_folder="Orders")
        storage.add_salesperson("Alice")
        path = storage.build_customer_dir("Alice", "CustomerA")
        # 应包含 "Orders" 这个自定义订单根名
        assert os.sep + "Orders" + os.sep in path
        # 不应再出现默认的 "1订单"
        assert "1订单" not in path


# ---------------------------------------------------------------
# Storage: _is_mid_layer_name
# ---------------------------------------------------------------
class TestIsMidLayerName:
    def test_default_keywords(self, storage):
        """默认关键词 ["进行", "订单"] 同时满足时返回 True。"""
        assert storage._is_mid_layer_name("进行中订单") is True
        assert storage._is_mid_layer_name("1.进行订单") is True

    def test_default_partial_keywords_returns_false(self, storage):
        """只含部分关键词时返回 False。"""
        assert storage._is_mid_layer_name("进行中") is False
        assert storage._is_mid_layer_name("订单列表") is False
        assert storage._is_mid_layer_name("其他文件夹") is False

    def test_custom_keywords(self, storage):
        """自定义关键词后按新规则判断。"""
        storage.update_config(mid_layer_keywords=["WIP"])
        assert storage._is_mid_layer_name("WIP Orders") is True
        assert storage._is_mid_layer_name("进行中订单") is False  # 不含 WIP

    def test_empty_keywords_always_false(self, storage):
        """关键词列表为空时，始终返回 False。"""
        storage.update_config(mid_layer_keywords=[])
        assert storage._is_mid_layer_name("进行中订单") is False
        assert storage._is_mid_layer_name("任何名字") is False


# ---------------------------------------------------------------
# Storage: set_root_dir 旧版 config 自动补写
# ---------------------------------------------------------------
class TestConfigUpgrade:
    def test_new_config_contains_defaults(self, tmp_root):
        """首次创建 config.json 时，应包含所有默认字段。"""
        s = Storage(str(tmp_root))
        cfg = s.load_config()
        assert cfg.get("order_root_folder") == DEFAULT_ORDER_ROOT_FOLDER
        assert cfg.get("mid_layer_keywords") == list(DEFAULT_MID_LAYER_KEYWORDS)
        assert cfg.get("origin_map") == DEFAULT_ORIGIN_MAP
        assert cfg.get("origin_file_ext") == DEFAULT_ORIGIN_FILE_EXT

    def test_legacy_config_gets_backfilled(self, tmp_root):
        """已存在但缺字段的 config.json 会在 set_root_dir 时自动补写。"""
        data_dir = tmp_root / ".order_tool"
        data_dir.mkdir(parents=True)
        config_file = data_dir / "config.json"
        # 模拟旧版：只有最早的几个字段
        legacy_cfg = {
            "root_dir": str(tmp_root),
            "template_files_dir": "",
            "last_salesperson": "",
            "last_customer": "",
            "last_order_type": "外贸",
            "last_product_category": "环氧树脂",
            "operator": "someone",
        }
        config_file.write_text(json.dumps(legacy_cfg, ensure_ascii=False),
                                encoding="utf-8")

        # 初始化 Storage 应触发自动补写
        s = Storage(str(tmp_root))
        cfg = s.load_config()
        # 旧字段保留
        assert cfg.get("operator") == "someone"
        # 新字段被补写
        assert cfg.get("order_root_folder") == DEFAULT_ORDER_ROOT_FOLDER
        assert cfg.get("mid_layer_keywords") == list(DEFAULT_MID_LAYER_KEYWORDS)
        assert cfg.get("origin_map") == DEFAULT_ORIGIN_MAP
        assert cfg.get("origin_file_ext") == DEFAULT_ORIGIN_FILE_EXT

    def test_existing_custom_values_not_overwritten(self, tmp_root):
        """已存在的自定义值不应被默认值覆盖。"""
        data_dir = tmp_root / ".order_tool"
        data_dir.mkdir(parents=True)
        config_file = data_dir / "config.json"
        custom_cfg = {
            "root_dir": str(tmp_root),
            "order_root_folder": "MyOrders",
            "mid_layer_keywords": ["进行中"],
            # origin_map / origin_file_ext 缺失 → 应被补写默认值
        }
        config_file.write_text(json.dumps(custom_cfg, ensure_ascii=False),
                                encoding="utf-8")

        s = Storage(str(tmp_root))
        cfg = s.load_config()
        # 自定义值保留
        assert cfg.get("order_root_folder") == "MyOrders"
        assert cfg.get("mid_layer_keywords") == ["进行中"]
        # 缺失的字段被默认值补写
        assert cfg.get("origin_map") == DEFAULT_ORIGIN_MAP
        assert cfg.get("origin_file_ext") == DEFAULT_ORIGIN_FILE_EXT


# ---------------------------------------------------------------
# Storage: scan 相关在 order_root_folder 改动后仍生效
# ---------------------------------------------------------------
class TestScanWithCustomOrderRoot:
    def test_scan_order_root_respects_config(self, storage, tmp_root):
        """scan_order_root 应扫描 config 指定的订单根文件夹。"""
        storage.update_config(order_root_folder="CustomOrders")
        order_root = tmp_root / "CustomOrders"
        order_root.mkdir()
        (order_root / "SalespersonA").mkdir()
        (order_root / "SalespersonB").mkdir()

        names = storage.scan_order_root()
        assert "SalespersonA" in names
        assert "SalespersonB" in names

    def test_scan_order_root_default_not_found_when_custom(
            self, storage, tmp_root):
        """自定义订单根名后，默认名 "1订单" 下的内容不会被返回。"""
        storage.update_config(order_root_folder="CustomOrders")
        # 同时建一个 1订单 文件夹（不该被扫描）
        (tmp_root / "1订单").mkdir()
        (tmp_root / "1订单" / "NotMe").mkdir()

        names = storage.scan_order_root()
        assert "NotMe" not in names


# ---------------------------------------------------------------
# build_context：<自定义编号> 占位符（替换原 <HRXY编号>）
# ---------------------------------------------------------------
def test_build_context_custom_no_placeholder():
    """build_context 应生成 <自定义编号> 键；不含已移除的 <HRXY编号>。"""
    order = {
        "order_no": "ORD001",
        "customer": "示例客户A",
        "custom_no": "X-123",
    }
    ctx = folder_builder.build_context(order)
    assert ctx["<自定义编号>"] == "X-123"
    assert "<HRXY编号>" not in ctx

    # custom_no 缺失时应为空串，占位符仍存在
    order2 = {"order_no": "ORD002", "customer": "B"}
    ctx2 = folder_builder.build_context(order2)
    assert ctx2.get("<自定义编号>") == ""


# ---------------------------------------------------------------
# execute_build 向后兼容：未传 origin_map/origin_file_ext 时使用默认值
# ---------------------------------------------------------------
def test_execute_build_backward_compat(tmp_root):
    """test_core.py 旧签名调用 execute_build 不传 origin_map/ext 也能跑。"""
    s = Storage(str(tmp_root))
    customer_dir = tmp_root / "customers" / "ACME"
    customer_dir.mkdir(parents=True)
    tpl = s.load_template("standard_export.json")
    order = {
        "order_type": "外贸",
        "order_no": "ORD-COMPAT",
        "customer": "ACME",
        "product_category": "环氧树脂",
        "salesperson": "张三",
        "needs_inspection": False,
    }
    # 不传 origin_map / origin_file_ext：应回退到默认映射
    result = folder_builder.execute_build(
        order=order, template=tpl, base_path=str(customer_dir),
        template_files_dir=None,
    )
    assert Path(result["base_path"]).is_dir()
    assert Path(result["checklist_path"]).is_file()
