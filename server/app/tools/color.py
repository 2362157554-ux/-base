"""调色：ffmpeg eq filter。"""
from __future__ import annotations
from pathlib import Path
from .base import BaseTool, ToolResult, ParamSpec, ParamType
from ..render.ffmpeg import is_available, _run


class ColorTool(BaseTool):
    name = "color"
    display_name = "调色"
    summary = "调亮度/对比度/饱和度（ffmpeg eq）。"

    def params_schema(self) -> list[ParamSpec]:
        return [
            ParamSpec("enabled", "启用", ParamType.BOOL, default=False),
            ParamSpec("brightness", "亮度", ParamType.FLOAT, default=0.0, min=-0.5, max=0.5),
            ParamSpec("contrast", "对比度", ParamType.FLOAT, default=1.0, min=0.5, max=2.0),
            ParamSpec("saturation", "饱和度", ParamType.FLOAT, default=1.0, min=0.0, max=2.0),
        ]

    def run(self, *, work_dir, upload_paths, params) -> ToolResult:
        if not params.get("enabled", False):
            return ToolResult(ok=True, message="color skipped")
        if not is_available():
            return ToolResult(ok=False, message="ffmpeg unavailable")
        src = params.get("source_video")
        if not src or not src.exists():
            return ToolResult(ok=False, message="color: need source_video")
        b = float(params.get("brightness", 0.0))
        c = float(params.get("contrast", 1.0))
        s = float(params.get("saturation", 1.0))
        out = work_dir / "color.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
               "-vf", f"eq=brightness={b:.3f}:contrast={c:.3f}:saturation={s:.3f}",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)]
        try:
            _run(cmd)
        except RuntimeError as e:
            return ToolResult(ok=False, message=f"color failed: {e}")
        return ToolResult(ok=True, output_path=out, message="color graded")