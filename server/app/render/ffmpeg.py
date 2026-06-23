"""ffmpeg 兜底渲染（自研实现）。

当用户机器上没有剪映、或者只想纯服务端出片时，把 DraftScript
按时间轴直接合成为 MP4。

实现思路：
- 把每个视频片段按 target_timerange 平铺到一个临时帧源；
- 用 ``image2`` demuxer 把片段 mp4 解成帧序列；
- 通过 ``filter_complex`` 做拼接 + 字幕烧录 + BGM 混音；
- 一次性输出最终 MP4。

代码全部本项目自写；不调用任何第三方 Python 视频库。
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ..draft import (
    DraftScript,
    TrackKind,
    MaterialKind,
    Timerange,
)


# ---------------------------------------------------------------------------
# 能力探测
# ---------------------------------------------------------------------------


def is_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _run(cmd: list[str]) -> None:
    """跑 ffmpeg，失败时抛错。"""
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed ({proc.returncode}): {proc.stderr[-2000:]}"
        )


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------


def compose_from_script(
    script: DraftScript,
    upload_paths: dict[str, Path],
    output_path: Path,
) -> Path:
    """把 DraftScript 合成成 MP4。

    当前实现的最小集：
    - 单视频片段 + 单 BGM + 文字字幕烧录
    - 复杂片段（多视频叠化）会在后续扩展
    """
    if not is_available():
        raise RuntimeError("ffmpeg not in PATH")

    # 收集视频片段 / 音频片段 / 文字片段
    video_segs: list[dict] = []
    audio_segs: list[dict] = []
    text_segs: list[dict] = []

    for track in script.tracks:
        for seg in track.segments:
            mat = script.materials.get(seg.material_id)
            if mat is None:
                continue
            entry = {"segment": seg, "material": mat}
            if track.kind == TrackKind.VIDEO and mat.kind == MaterialKind.VIDEO:
                video_segs.append(entry)
            elif track.kind == TrackKind.AUDIO and mat.kind == MaterialKind.AUDIO:
                audio_segs.append(entry)
            elif track.kind == TrackKind.TEXT and mat.kind == MaterialKind.TEXT:
                text_segs.append(entry)

    # 1) 选主视频源（第一个真实视频片段；若只有 placeholder 则生成纯色）
    main_video = next(
        (e for e in video_segs if not e["material"].local_path.startswith("placeholder://")),
        None,
    )

    width, height = script.width or 1080, script.height or 1920
    fps = script.fps or 30
    duration = script.total_duration_us() / 1_000_000 or 6.0

    inputs: list[str] = []
    filter_parts: list[str] = []

    if main_video is None:
        # 无视频：生成纯色 + drawtext
        inputs.extend(["-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:r={fps}:d={duration}"])
        video_src = "0:v"
    else:
        src = upload_paths.get(f"/api/files/{Path(main_video['material'].local_path).name}")
        if src is None:
            # 可能是 placeholder 占位但带真实素材路径
            src = Path(main_video["material"].local_path)
        inputs.extend(["-ss", "0", "-t", str(duration), "-i", str(src)])
        video_src = "0:v"

    # 2) 缩放到画布
    filter_parts.append(
        f"[{video_src}]scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[v0]"
    )

    last_v = "v0"

    # 3) 烧录字幕
    for i, t in enumerate(text_segs):
        start = t["segment"].target.start_us / 1_000_000
        dur = t["segment"].target.duration_us / 1_000_000
        content = (t["material"].content or "").replace(":", "\\:").replace("'", "\\'")
        if not content.strip():
            continue
        out_label = f"vt{i}"
        # 中文字体兜底用 Source Han Sans / Noto；本机没装会回落到默认字体
        font_arg = "fontfile=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        draw = (
            f"drawtext={font_arg}:text='{content}':"
            f"fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-180:"
            f"enable='between(t,{start:.3f},{start+dur:.3f})'"
        )
        filter_parts.append(f"[{last_v}]{draw}[{out_label}]")
        last_v = out_label

    # 4) 收集 BGM
    audio_labels: list[str] = []
    for idx, a in enumerate(audio_segs):
        start_in = a["segment"].source.start_us / 1_000_000
        target_start = a["segment"].target.start_us / 1_000_000
        target_dur = a["segment"].target.duration_us / 1_000_000
        src_path = upload_paths.get(f"/api/files/{Path(a['material'].local_path).name}") \
            or Path(a["material"].local_path)
        inputs.extend(["-ss", str(start_in), "-t", str(target_dur), "-i", str(src_path)])
        label = f"a{idx}"
        audio_labels.append((label, target_start, target_dur))

    if audio_labels:
        # 混音：把多段 BGM 排到时间轴上再 amix
        mix_inputs: list[str] = []
        for idx, (label, t_start, t_dur) in enumerate(audio_labels):
            delay_ms = int(t_start * 1000)
            # adelay 默认毫秒
            mix_inputs.append(f"[{idx+1}:a]adelay={delay_ms}|{delay_ms},apad=whole_dur={duration}[{label}]")
        filter_parts.extend(mix_inputs)
        concat_label = "amixall"
        if len(audio_labels) == 1:
            filter_parts.append(
                f"[{audio_labels[0][0]}]atrim=0:{duration},asetpts=PTS-STARTPTS[aout]"
            )
        else:
            joined = "".join(f"[{lbl}]" for lbl, _, _ in audio_labels)
            filter_parts.append(
                f"{joined}amix=inputs={len(audio_labels)}:duration=longest,"
                f"atrim=0:{duration},asetpts=PTS-STARTPTS[aout]"
            )

    # 5) 拼装 filter_complex
    filter_complex = ";".join(filter_parts)
    cmd: list[str] = ["ffmpeg", "-y", "-loglevel", "error"]
    cmd.extend(inputs)
    cmd.extend(["-filter_complex", filter_complex])
    cmd.extend(["-map", f"[{last_v}]"])
    if audio_labels:
        cmd.extend(["-map", "[aout]"])
    cmd.extend(
        [
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-t", str(duration),
        ]
    )
    if audio_labels:
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])
    cmd.append(str(output_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run(cmd)
    return output_path