"""工具注册表。新增 tool = 写一个文件 + 在下面 register 一行。"""
from __future__ import annotations
from .base import BaseTool, ToolResult
from .compose import ComposeTool
from .subtitle import SubtitleStyleTool
from .concat import ConcatTool
from .transition import TransitionTool
from .color import ColorTool

REGISTRY: dict[str, BaseTool] = {}


def register(tool: BaseTool) -> None:
    if not tool.name:
        raise ValueError(f"tool {tool!r} missing name")
    REGISTRY[tool.name] = tool


register(ComposeTool())          # 基线主出片
register(SubtitleStyleTool())    # 字幕样式增强
register(ConcatTool())           # 多段拼接
register(TransitionTool())       # 转场
register(ColorTool())            # 调色


def get_tool(name: str) -> BaseTool:
    if name not in REGISTRY:
        raise KeyError(f"tool not found: {name}")
    return REGISTRY[name]


def list_tools() -> list[dict]:
    out = []
    for t in REGISTRY.values():
        out.append({
            "name": t.name,
            "display_name": t.display_name,
            "summary": t.summary,
            "requires_ffmpeg": t.requires_ffmpeg,
            "minVideoInputs": t.min_video_inputs,
            "maxVideoInputs": t.max_video_inputs,
            "params": [
                {"key": p.key, "label": p.label, "type": p.type.value,
                 "default": p.default, "choices": list(p.choices),
                 "min": p.min, "max": p.max, "help": p.help}
                for p in t.params_schema()
            ],
        })
    return out


__all__ = ["REGISTRY", "get_tool", "list_tools", "ToolResult"]
