"""本地自测：不开 uvicorn，验证 draft / render 单元链路。

跑法：
    cd server
    python -m smoke_test
"""
from __future__ import annotations

import json
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.draft import (
    DraftScript,
    Material,
    TextMaterial,
    MaterialKind,
    TrackKind,
    Timerange,
)


def test_draft_json_roundtrip() -> None:
    script = DraftScript(
        name="smoke",
        width=1080,
        height=1920,
        fps=30,
        create_time=int(time.time()),
    )
    mat = Material(
        kind=MaterialKind.VIDEO,
        local_path="uploads/abc.mp4",
        duration_us=5_000_000,
        width=1080,
        height=1920,
    )
    script.add_segment_to(
        TrackKind.VIDEO,
        mat,
        Timerange.from_seconds(0.0, 5.0),
    )

    text = TextMaterial(kind=MaterialKind.TEXT, content="你好，世界")
    script.add_segment_to(
        TrackKind.TEXT,
        text,
        Timerange.from_seconds(1.0, 2.0),
    )

    j = script.to_json()
    assert j["canvas_config"]["width"] == 1080
    assert len(j["tracks"]) == 2
    assert j["materials"]["videos"][0]["path"] == "uploads/abc.mp4"
    assert j["materials"]["texts"][0]["content"] == "你好，世界"
    print("[ok] draft.json schema is well-formed:", json.dumps(j, ensure_ascii=False)[:200], "...")


def test_draft_zip_packing(tmp: Path) -> None:
    script = DraftScript(name="zip-test", width=720, height=1280, fps=30, create_time=1)
    mat = Material(kind=MaterialKind.VIDEO, local_path="x.mp4", duration_us=2_000_000)
    script.add_segment_to(TrackKind.VIDEO, mat, Timerange.from_seconds(0.0, 2.0))

    # 直接复用 routes._zip_draft 的逻辑
    from app.api.routes import _zip_draft
    blob = _zip_draft(script)
    out = tmp / "draft.zip"
    out.write_bytes(blob)
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert "zip-test/draft_content.json" in names
        assert "zip-test/draft.meta_info" in names
    print("[ok] draft zip packs:", names)


def main() -> None:
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="base-smoke-"))
    test_draft_json_roundtrip()
    test_draft_zip_packing(tmp)
    print("all smoke tests passed; tmp =", tmp)


if __name__ == "__main__":
    main()