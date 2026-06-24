"""注册表测试。"""
from app.tools import REGISTRY, get_tool, list_tools
from app.tools.registry import register
from app.tools.base import BaseTool, ToolResult, ParamSpec, ParamType


def test_registry_has_five_tools():
    """当前已注册 5 个 tool：compose / subtitle / concat / transition / color。"""
    assert set(REGISTRY.keys()) == {"compose", "subtitle", "concat", "transition", "color"}


def test_get_tool_known_and_unknown():
    assert get_tool("subtitle").name == "subtitle"
    import pytest
    with pytest.raises(KeyError):
        get_tool("nonexistent")


def test_list_tools_schema_shape():
    """list_tools 返回的每条都带 name/display_name/summary/params。"""
    tools = list_tools()
    assert len(tools) == 5
    for t in tools:
        assert {"name", "display_name", "summary", "params"}.issubset(t.keys())
        assert isinstance(t["params"], list)
        for p in t["params"]:
            assert {"key", "label", "type", "default", "choices"}.issubset(p.keys())


def test_register_rejects_empty_name():
    class _Anon(BaseTool):
        name = ""
        display_name = "x"
        summary = "x"

        def params_schema(self): return []
        def run(self, *, work_dir, upload_paths, params): return ToolResult(ok=True)

    import pytest
    with pytest.raises(ValueError):
        register(_Anon())
