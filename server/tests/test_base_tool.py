"""BaseTool 抽象类的结构测试。"""
from app.tools.base import BaseTool, ToolResult, ParamSpec, ParamType


def test_param_spec_is_frozen():
    """ParamSpec 是 frozen dataclass，不能就地改。"""
    p = ParamSpec(key="x", label="X", type=ParamType.INT, default=0)
    import dataclasses
    try:
        p.key = "y"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("ParamSpec should be frozen")


def test_param_type_enum_values():
    """ParamType 的字符串值就是给前端的 type 字段。"""
    assert ParamType.BOOL.value == "bool"
    assert ParamType.INT.value == "int"
    assert ParamType.FLOAT.value == "float"
    assert ParamType.TEXT.value == "text"
    assert ParamType.CHOICE.value == "choice"
    assert ParamType.FILE.value == "file"


def test_tool_result_defaults():
    """ToolResult 默认字段：ok=False、output_path=None、message 空串。"""
    r = ToolResult(ok=True)
    assert r.ok is True
    assert r.output_path is None
    assert r.message == ""
    assert r.data == {}


def test_base_tool_is_abstract():
    """BaseTool 不能直接实例化（缺 params_schema/run）。"""
    import pytest
    with pytest.raises(TypeError):
        BaseTool()  # type: ignore[abstract]
