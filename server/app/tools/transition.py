"""转场：两段视频之间加 xfade。"""
from __future__ import annotations
from pathlib import Path
import subprocess
from .base import BaseTool, ToolResult, ParamSpec, ParamType
from ..render.ffmpeg import is_available, _run


# ffmpeg xfade 内置（节选常用）
TRANSITIONS = ("fade", "fadeblack", "fadewhite",
               "wipeleft", "wiperight", "slideup", "slidedown")


class TransitionTool(BaseTool):
    name = "transition"
    display_name = "转场"
    summary = "在两段视频之间加转场（xfade）。"

    def params_schema(self) -> list[ParamSpec]:
        return [
            ParamSpec("enabled", "启用", ParamType.BOOL, default=True),
            ParamSpec("kind", "类型", ParamType.CHOICE, default="fade", choices=TRANSITIONS),
            ParamSpec("duration_s", "时长(秒)", ParamType.FLOAT, default=0.8, min=0.1, max=3.0),
        ]

    def run(self, *, work_dir, upload_paths, params) -> ToolResult:
        if not params.get("enabled", True):
            return ToolResult(ok=True, message="transition skipped")
        if not is_available():
            return ToolResult(ok=False, message="ffmpeg unavailable")
        urls = params.get("videos") or []
        if len(urls) != 2:
            return ToolResult(ok=False, message="transition needs exactly 2 videos")
        paths = [ConcatTool._resolve(u, upload_paths) for u in urls]
        if any(p is None for p in paths):
            return ToolResult(ok=False, message="missing upload(s)")
        paths = [p for p in paths if p]  # type: ignore

        kind = params.get("kind", "fade")
        dur = float(params.get("duration_s", 0.8))
        # 探测第一段时长算 xfade offset
        try:
            d0 = float(subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(paths[0])]
            ).strip() or b"6")
        except Exception:
            d0 = 6.0

        out = work_dir / "transition.mp4"
        scale = ("scale=720:1280:force_original_aspect_ratio=decrease,"
                 "pad=720:1280:(ow-iw)/2:(oh-ih)/2:black,setsar=1")
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-i", str(paths[0]), "-i", str(paths[1]),
               "-filter_complex",
               f"[0:v]{scale}[v0];[1:v]{scale}[v1];"
               f"[v0][v1]xfade=transition={kind}:duration={dur}:offset={max(d0-dur,0):.3f}[vx]",
               "-map", "[vx]", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
        try:
            _run(cmd)
        except RuntimeError as e:
            return ToolResult(ok=False, message=f"transition failed: {e}")
        return ToolResult(ok=True, output_path=out, message=f"xfade {kind}")