"""Draft zip packaging tests."""
import json
import zipfile

from app.draft import DraftScript, Material, MaterialKind, Timerange, TrackKind
from app.draft.packaging import inspect_draft_zip, zip_draft


def test_zip_draft_can_include_media_and_cover(tmp_path):
    storage_root = tmp_path / "storage"
    upload = storage_root / "uploads" / "a.mp4"
    upload.parent.mkdir(parents=True)
    upload.write_bytes(b"fake mp4 bytes")

    script = DraftScript(name="draft-test", width=720, height=1280, fps=30, create_time=1)
    mat = Material(
        kind=MaterialKind.VIDEO,
        local_path="uploads/a.mp4",
        duration_us=1_000_000,
        width=720,
        height=1280,
    )
    script.add_segment_to(TrackKind.VIDEO, mat, Timerange.from_seconds(0, 1))

    blob = zip_draft(script, storage_root=storage_root, include_media=True)
    out = tmp_path / "draft.zip"
    out.write_bytes(blob)

    with zipfile.ZipFile(out) as z:
        names = set(z.namelist())
        content = json.loads(z.read("draft-test/draft_content.json"))

    assert "draft-test/materials/a.mp4" in names
    assert "draft-test/draft_cover.jpg" in names
    assert content["materials"]["videos"][0]["path"] == "materials/a.mp4"


def test_inspect_draft_zip_reports_referenced_media(tmp_path):
    storage_root = tmp_path / "storage"
    upload = storage_root / "uploads" / "a.mp4"
    upload.parent.mkdir(parents=True)
    upload.write_bytes(b"fake mp4 bytes")

    script = DraftScript(name="draft-test", width=720, height=1280, fps=30, create_time=1)
    mat = Material(kind=MaterialKind.VIDEO, local_path="uploads/a.mp4", duration_us=1_000_000)
    script.add_segment_to(TrackKind.VIDEO, mat, Timerange.from_seconds(0, 1))

    report = inspect_draft_zip(zip_draft(script, storage_root=storage_root, include_media=True))

    assert report["ok"] is True
    assert report["missing_media"] == []
