"""路由层：把前端 HTTP 请求翻译成对 draft/render 模块的调用。"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from .schemas import (
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
)

from ..draft import (
    DraftScript,
    Material,
    TextMaterial,
    MaterialKind,
    TrackKind,
    Timerange,
)
from ..draft.packaging import inspect_draft_zip, zip_draft
from ..render import ffmpeg as ffmpeg_mod
from ..render import remotion as remotion_mod
from ..tools import list_tools, get_tool


router = APIRouter(tags=["base"])


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------


STORAGE_ROOT = Path(os.environ.get("STORAGE_ROOT", "./storage")).resolve()
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = STORAGE_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = STORAGE_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(200 * 1024 * 1024)))


# ---------------------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------------------


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        ffmpeg_available=ffmpeg_mod.is_available(),
        remotion_available=remotion_mod.is_available(),
        time=time.time(),
    )


# ---------------------------------------------------------------------------
# 上传（前端把素材传到后端存盘）
# ---------------------------------------------------------------------------


@router.post("/uploads")
async def upload_file(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(400, "missing filename")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".mp4", ".mov", ".png", ".jpg", ".jpeg", ".mp3", ".wav", ".m4a"}:
        raise HTTPException(400, f"unsupported file type: {suffix}")
    name = f"{uuid.uuid4().hex[:12]}{suffix}"
    dest = UPLOAD_DIR / name
    written = 0
    try:
        with dest.open("wb") as f:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, f"file too large; max {MAX_UPLOAD_BYTES} bytes")
                f.write(chunk)
    except Exception:
        if dest.exists():
            dest.unlink()
        raise
    return {
        "filename": name,
        "url": f"/api/files/{name}",
        "size": dest.stat().st_size,
    }


@router.get("/files/{name}")
def get_file(name: str):
    p = UPLOAD_DIR / name
    if not p.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(p)


# ---------------------------------------------------------------------------
# 核心：生成草稿 / 出片
# ---------------------------------------------------------------------------


def _build_script(req: GenerateRequest, upload_paths: dict[str, Path]) -> DraftScript:
    """把请求转成 DraftScript（不调剪映、不写文件）。"""
    script = DraftScript(
        name=f"base-{uuid.uuid4().hex[:8]}",
        width=req.width,
        height=req.height,
        fps=req.fps,
        create_time=int(time.time()),
    )

    # 一段主视频轨道：把第一个视频片段撑满总时长
    video_items = [c for c in req.clips if c.kind == "video"]
    audio_items = [c for c in req.clips if c.kind == "audio"]

    if video_items:
        first = video_items[0]
        path = upload_paths[first.url]  # type: ignore[arg-type]
        mat = Material(
            kind=MaterialKind.VIDEO,
            local_path=str(path.relative_to(STORAGE_ROOT)),
            duration_us=int((first.duration_s or req.total_duration_s) * 1_000_000),
            width=first.width or req.width,
            height=first.height or req.height,
        )
        script.add_segment_to(
            TrackKind.VIDEO,
            mat,
            Timerange.from_seconds(0.0, req.total_duration_s),
            source=Timerange.from_seconds(0.0, req.total_duration_s),
            intro="fade_in",
        )
    else:
        # 无视频也要让草稿合法：放一个纯色 placeholder（路径 B 会用 ffmpeg 兜底生成）
        placeholder = Material(
            kind=MaterialKind.VIDEO,
            local_path="placeholder://solid",
            duration_us=int(req.total_duration_s * 1_000_000),
            width=req.width,
            height=req.height,
        )
        script.add_segment_to(
            TrackKind.VIDEO,
            placeholder,
            Timerange.from_seconds(0.0, req.total_duration_s),
        )

    # 音频轨道
    for a in audio_items:
        if not a.url:
            continue
        path = upload_paths[a.url]
        mat = Material(
            kind=MaterialKind.AUDIO,
            local_path=str(path.relative_to(STORAGE_ROOT)),
            duration_us=int((a.duration_s or req.total_duration_s) * 1_000_000),
        )
        script.add_segment_to(
            TrackKind.AUDIO,
            mat,
            Timerange.from_seconds(0.0, req.total_duration_s),
            volume=0.85,
        )

    # 字幕（拆分一句话）
    parts = [p.strip() for p in req.text.replace("。", ".").replace("，", ",").splitlines() if p.strip()]
    if not parts:
        parts = [req.text]
    step = req.total_duration_s / max(len(parts), 1)
    for i, line in enumerate(parts):
        mat = TextMaterial(
            kind=MaterialKind.TEXT,
            local_path="",          # 文本素材无路径
            content=line,
        )
        script.add_segment_to(
            TrackKind.TEXT,
            mat,
            Timerange.from_seconds(i * step, step),
            intro="fade_in",
        )

    return script


@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    if not req.clips and not req.text:
        raise HTTPException(400, "need at least one of clips / text")

    # 把 url 映射到本地路径
    upload_paths: dict[str, Path] = {}
    for c in req.clips:
        if c.url and c.kind in {"video", "audio"}:
            name = Path(c.url).name
            p = UPLOAD_DIR / name
            if not p.is_file():
                raise HTTPException(400, f"uploaded file not found: {c.url}")
            upload_paths[c.url] = p

    script = _build_script(req, upload_paths)
    job_id = uuid.uuid4().hex[:12]

    if req.prefer_path == "draft":
        data = zip_draft(script, storage_root=STORAGE_ROOT, include_media=True)
        out = OUTPUT_DIR / f"{job_id}.draft.zip"
        out.write_bytes(data)
        return GenerateResponse(
            job_id=job_id,
            path="draft",
            artifact_url=f"/api/outputs/{out.name}",
            message="解压到剪映草稿目录（File/Draft/），剪映打开即可批量导出。",
        )

    if req.prefer_path == "remotion":
        if not remotion_mod.is_available():
            raise HTTPException(
                503,
                "remotion unavailable; run npm ci in web/ or switch prefer_path='ffmpeg'",
            )
        out = OUTPUT_DIR / f"{job_id}.remotion.mp4"
        try:
            remotion_mod.render_base_clip(
                text=req.text,
                width=req.width,
                height=req.height,
                fps=req.fps,
                duration_s=req.total_duration_s,
                output_path=out,
            )
        except RuntimeError as e:
            raise HTTPException(500, str(e)) from e
        return GenerateResponse(
            job_id=job_id,
            path="remotion",
            artifact_url=f"/api/outputs/{out.name}",
            message="Remotion 组合渲染出的 MP4",
        )

    # 路径 B：ffmpeg 兜底
    if not ffmpeg_mod.is_available():
        raise HTTPException(
            503,
            "ffmpeg unavailable; install ffmpeg or switch prefer_path='draft'",
        )
    out = OUTPUT_DIR / f"{job_id}.mp4"
    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    selected: list[str] = []
    tool_logs: list[str] = []

    # Stage 1：上游（concat/transition）从用户素材产出"主视频"
    main_video: Path | None = None
    for tname in ("concat", "transition"):
        raw_params = (req.tools or {}).get(tname)
        if raw_params is None:
            continue
        tparams = dict(raw_params)
        selected.append(tname)
        res = get_tool(tname).run(work_dir=work_dir, upload_paths=upload_paths,
                                 params=tparams)
        tool_logs.append(f"[{tname}] {res.message}")
        if not res.ok: raise HTTPException(500, "; ".join(tool_logs))
        if res.output_path: main_video = res.output_path

    # Stage 2：基线 compose 永远跑；上游产了新主视频就替换原脚本里的视频轨
    if main_video is not None:
        for tr in script.tracks:
            if tr.kind == TrackKind.VIDEO:
                tr.segments.clear()
        mat = Material(kind=MaterialKind.VIDEO, local_path=str(main_video),
            duration_us=int(req.total_duration_s * 1_000_000),
            width=req.width, height=req.height)
        script.add_segment_to(TrackKind.VIDEO, mat,
            Timerange.from_seconds(0.0, req.total_duration_s),
            source=Timerange.from_seconds(0.0, req.total_duration_s))
        upload_paths["__main__"] = main_video
    baseline = work_dir / "compose.mp4"
    ffmpeg_mod.compose_from_script(script, upload_paths, baseline)
    last_out: Path = baseline

    # Stage 3：后处理（color/subtitle）链式叠加，拿上一个 output
    for tname in ("color", "subtitle"):
        raw_params = (req.tools or {}).get(tname)
        if raw_params is None:
            continue
        tparams = dict(raw_params)
        selected.append(tname)
        tparams["source_video"] = last_out
        tparams.setdefault("duration_s", req.total_duration_s)
        if tname == "subtitle":
            tparams.setdefault("lines", [s.strip() for s in
                req.text.replace("。", ".").replace("，", ",").splitlines() if s.strip()]
                or [req.text])
        res = get_tool(tname).run(work_dir=work_dir, upload_paths=upload_paths, params=tparams)
        tool_logs.append(f"[{tname}] {res.message}")
        if not res.ok: raise HTTPException(500, "; ".join(tool_logs))
        if res.output_path: last_out = res.output_path

    import shutil as _sh; _sh.copyfile(last_out, out)
    msg = "ffmpeg 直接合成的 MP4（tools: " + ", ".join(selected) + "）" if selected else "ffmpeg 直接合成的 MP4"
    return GenerateResponse(job_id=job_id, path="ffmpeg",
        artifact_url=f"/api/outputs/{out.name}", message=msg)


@router.get("/outputs/{name}")
def get_output(name: str):
    p = OUTPUT_DIR / name
    if not p.is_file():
        raise HTTPException(404, "not found")
    media = "application/zip" if name.endswith(".zip") else "video/mp4"
    return FileResponse(p, media_type=media, filename=name)


@router.get("/outputs/{name}/inspect")
def inspect_output(name: str) -> dict:
    p = OUTPUT_DIR / name
    if not p.is_file():
        raise HTTPException(404, "not found")
    if not name.endswith(".zip"):
        raise HTTPException(400, "only draft zip outputs can be inspected")
    return inspect_draft_zip(p.read_bytes())


# ---------------------------------------------------------------------------
# BaseTool 能力发现（前端拉这个去动态渲染开关面板）
# ---------------------------------------------------------------------------


@router.get("/tools")
def tools_index() -> dict:
    return {"tools": list_tools()}
