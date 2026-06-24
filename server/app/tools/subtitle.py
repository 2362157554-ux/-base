"""字幕样式增强：source_video + lines → 烧录字幕后的 mp4。"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .base import BaseTool, ToolResult, ParamSpec, ParamType
from ..render.ffmpeg import is_available, _run


# 优先级：微软雅黑 → Noto CJK → macOS PingFang
_FONTS = (
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
)


def _pick_font() -> str | None:
    return next((f for f in _FONTS if Path(f).exists()), None)


class SubtitleStyleTool(BaseTool):
    name = "subtitle"
    display_name = "字幕样式"
    summary = "把字幕烧录成可定制的样式（颜色/字号/位置/阴影）。"

    def params_schema(self) -> list[ParamSpec]:
        return [
            ParamSpec("enabled", "启用", ParamType.BOOL, default=True),
            ParamSpec("font_size", "字号", ParamType.INT, default=56, min=16, max=160),
            ParamSpec("color", "字色", ParamType.CHOICE, default="white",
                      choices=("white", "yellow", "black", "red")),
            ParamSpec("position", "位置", ParamType.CHOICE, default="bottom",
                      choices=("bottom", "middle", "top")),
            ParamSpec("shadow", "加阴影", ParamType.BOOL, default=True),
        ]

    def run(self, *, work_dir, upload_paths, params) -> ToolResult:
        if not params.get("enabled", True):
            return ToolResult(ok=True, message="subtitle skipped")
        if not is_available():
            return ToolResult(ok=False, message="ffmpeg unavailable")
        src: Path | None = params.get("source_video")
        lines: list[str] = params.get("lines") or []
        if not src or not lines or not src.exists():
            return ToolResult(ok=False, message="need source_video + lines")

        font = _pick_font()
        # ffmpeg filter 语法：value 里的 ":" 要转；整个路径用单引号包
        font_arg = (f"fontfile='{font.replace(chr(92), '/').replace(':', chr(92)+':')}':"
                    if font else "")
        color = {"white": "white", "yellow": "0xFFFF66",
                 "black": "black", "red": "0xFF4444"}.get(params.get("color", "white"), "white")
        y = {"bottom": "h-180", "middle": "(h-text_h)/2", "top": "100"}.get(
            params.get("position", "bottom"), "h-180")
        sz = int(params.get("font_size", 56))
        shadow = "shadowcolor=black@0.6:shadowx=2:shadowy=2:" if params.get("shadow", True) else ""

        dur = float(params.get("duration_s", 6.0))
        step = dur / max(len(lines), 1)
        chain, last = [], "0:v"
        for i, line in enumerate(lines):
            # 文本里的 \ : , ' 都要转
            t = (line.replace(chr(92), chr(92)+chr(92))
                     .replace(":", chr(92)+":")
                     .replace(",", chr(92)+",")
                     .replace("'", chr(92)+"'"))
            chain.append(
                f"[{last}]drawtext={font_arg}text='{t}':fontcolor={color}:"
                f"fontsize={sz}:x=(w-text_w)/2:y={y}:{shadow}"
                f"enable='between(t,{i*step:.3f},{(i+1)*step:.3f})'[v{i}]"
            )
            last = f"v{i}"

        out = work_dir / "subtitle.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
               "-filter_complex", ";".join(chain), "-map", f"[{last}]",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", str(dur), str(out)]
        try:
            _run(cmd)
        except RuntimeError as e:
            return ToolResult(ok=False, message=f"subtitle failed: {e}")
        return ToolResult(ok=True, output_path=out, message="subtitle burned")