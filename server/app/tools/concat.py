"""多段拼接。ffmpeg-only：concat filter（支持不同分辨率）或 demuxer。"""
from __future__ import annotations
from pathlib import Path
from .base import BaseTool, ToolResult, ParamSpec, ParamType
from ..render.ffmpeg import is_available, _run


class ConcatTool(BaseTool):
    name = "concat"
    display_name = "拼接"
    summary = "把 ≥2 段视频按顺序拼成一段。"

    def params_schema(self) -> list[ParamSpec]:
        return [
            ParamSpec("enabled", "启用", ParamType.BOOL, default=True),
            ParamSpec("mode", "方式", ParamType.CHOICE, default="concat_filter",
                      choices=("concat_filter", "concat_demuxer"),
                      help="filter 支持不同分辨率；demuxer 要求参数一致"),
        ]

    def run(self, *, work_dir, upload_paths, params) -> ToolResult:
        if not params.get("enabled", True):
            return ToolResult(ok=True, message="concat skipped")
        if not is_available():
            return ToolResult(ok=False, message="ffmpeg unavailable")
        urls = params.get("videos") or []
        if len(urls) < 2:
            return ToolResult(ok=False, message="concat needs >=2 videos")
        paths = [self._resolve(u, upload_paths) for u in urls]
        if any(p is None for p in paths):
            return ToolResult(ok=False, message="missing upload(s)")
        paths = [p for p in paths if p]  # type: ignore

        out = work_dir / "concat.mp4"
        mode = params.get("mode", "concat_filter")
        if mode == "concat_demuxer":
            lst = work_dir / "concat.list"
            lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in paths), "utf-8")
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                   "-safe", "0", "-i", str(lst), "-c", "copy", str(out)]
        else:
            inputs = [x for p in paths for x in ("-i", str(p))]
            scales = ";".join(
                f"[{i}:v]scale=720:1280:force_original_aspect_ratio=decrease,"
                f"pad=720:1280:(ow-iw)/2:(oh-ih)/2:black,setsar=1[v{i}]"
                for i in range(len(paths)))
            join = "".join(f"[v{i}]" for i in range(len(paths)))
            chain = f"{scales};{join}concat=n={len(paths)}:v=1:a=0[outv]"
            cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs,
                   "-filter_complex", chain, "-map", "[outv]",
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
        try:
            _run(cmd)
        except RuntimeError as e:
            return ToolResult(ok=False, message=f"concat failed: {e}")
        return ToolResult(ok=True, output_path=out, message=f"concat {len(paths)} clips")

    @staticmethod
    def _resolve(url: str, upload_paths: dict) -> Path | None:
        name = Path(url).name
        p = upload_paths.get(url) or upload_paths.get(f"/api/files/{name}")
        return p if p and p.exists() else None