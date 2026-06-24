"""主出片：把现有 compose_from_script 包成 BaseTool。"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .base import BaseTool, ToolResult, ParamSpec, ParamType
from ..render.ffmpeg import compose_from_script, is_available


class ComposeTool(BaseTool):
    name = "compose"
    display_name = "主出片（ffmpeg 兜底）"
    summary = "把视频+字幕+BGM 合成 MP4，纯服务端出片。"

    def params_schema(self) -> list[ParamSpec]:
        return []  # 全部走 GenerateRequest 顶层字段

    def run(self, *, work_dir: Path,
            upload_paths: dict, params: dict) -> ToolResult:
        if not is_available():
            return ToolResult(ok=False, message="ffmpeg 不在 PATH")
        from ..draft.schema import DraftScript  # 局部 import 避免环
        script: DraftScript = params["script"]
        out = work_dir / "compose.mp4"
        try:
            compose_from_script(script, upload_paths, out)
        except Exception as e:
            return ToolResult(ok=False, message=f"compose failed: {e}")
        return ToolResult(ok=True, output_path=out, message="主出片完成。")