"""Remotion renderer bridge.

This module lets the FastAPI server ask the web/ Remotion project to render the
same BaseClip composition that the browser previews.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def default_web_root() -> Path:
    """Return the repository web/ directory for the normal project layout."""
    return Path(__file__).resolve().parents[3] / "web"


def is_available(web_root: Path | None = None) -> bool:
    """Check whether local Remotion dependencies are installed."""
    root = web_root or Path(os.environ.get("WEB_ROOT", default_web_root()))
    bin_name = "remotion.cmd" if os.name == "nt" else "remotion"
    return (
        shutil.which("npm") is not None
        and (root / "package.json").is_file()
        and (root / "node_modules" / ".bin" / bin_name).is_file()
    )


def build_remotion_command(
    *,
    web_root: Path,
    composition_id: str,
    props_path: Path,
    output_path: Path,
) -> list[str]:
    entrypoint = Path("src") / "remotion" / "index.ts"
    npm = "npm.cmd" if os.name == "nt" else "npm"
    return [
        npm,
        "exec",
        "--",
        "remotion",
        "render",
        entrypoint.as_posix(),
        composition_id,
        str(output_path),
        "--props",
        str(props_path),
        "--overwrite",
    ]


def render_base_clip(
    *,
    text: str,
    width: int,
    height: int,
    fps: int,
    duration_s: float,
    output_path: Path,
    web_root: Path | None = None,
) -> Path:
    root = web_root or Path(os.environ.get("WEB_ROOT", default_web_root()))
    if not is_available(root):
        raise RuntimeError("Remotion dependencies are not installed; run npm ci in web/")

    lines = [
        part.strip()
        for part in text.replace("。", "\n").replace("，", "\n").replace(",", "\n").splitlines()
        if part.strip()
    ] or [text]
    props = {
        "lines": lines,
        "durationS": duration_s,
        "width": width,
        "height": height,
        "fps": fps,
        "background": "#0e0f13",
        "accentColor": "#4f8cff",
        "stickerEmoji": "*",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    props_dir = root / ".remotion-props"
    render_dir = root / ".remotion-renders"
    props_dir.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)
    props_path = props_dir / f"{output_path.stem}.json"
    render_path = render_dir / output_path.name
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")

    cmd = build_remotion_command(
        web_root=root,
        composition_id="base-clip",
        props_path=props_path.relative_to(root),
        output_path=render_path.relative_to(root),
    )
    proc = subprocess.run(
        cmd,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"remotion failed ({proc.returncode}): {proc.stderr[-2000:]}")
    shutil.copyfile(render_path, output_path)
    return output_path
