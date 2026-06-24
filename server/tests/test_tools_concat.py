"""concat tool 端到端：造 2 段 mp4 → concat filter → 验证产物。"""
import shutil
import subprocess

import pytest

from app.tools.concat import ConcatTool


pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg unavailable"
)


def _is_mp4(p) -> bool:
    return p.exists() and p.read_bytes()[4:8] == b"ftyp"


def test_concat_filter_mode(work_dir, upload_paths, make_test_mp4):
    """concat_filter 模式：2 段同分辨率 mp4 → 一段。"""
    a = make_test_mp4(work_dir / "a.mp4", dur=1.0, color="red")
    b = make_test_mp4(work_dir / "b.mp4", dur=1.0, color="blue")
    upload_paths["/api/files/a.mp4"] = a
    upload_paths["/api/files/b.mp4"] = b

    res = ConcatTool().run(
        work_dir=work_dir,
        upload_paths=upload_paths,
        params={"enabled": True, "mode": "concat_filter",
                "videos": ["/api/files/a.mp4", "/api/files/b.mp4"]},
    )
    assert res.ok, res.message
    assert res.output_path and _is_mp4(res.output_path)


def test_concat_requires_two_videos(work_dir, upload_paths):
    res = ConcatTool().run(
        work_dir=work_dir,
        upload_paths=upload_paths,
        params={"enabled": True, "videos": ["/api/files/only_one.mp4"]},
    )
    assert not res.ok
    assert ">=2" in res.message


def test_concat_disabled_is_noop(work_dir, upload_paths):
    res = ConcatTool().run(
        work_dir=work_dir,
        upload_paths=upload_paths,
        params={"enabled": False, "videos": ["/api/files/a.mp4"]},
    )
    assert res.ok and "skipped" in res.message
