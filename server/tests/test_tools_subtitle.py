"""subtitle tool 测试：在 mp4 上烧一行字幕。"""
import shutil

import pytest

from app.tools.subtitle import SubtitleStyleTool


pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg unavailable"
)


def test_subtitle_burns_one_line(work_dir, upload_paths, make_test_mp4):
    src = make_test_mp4(work_dir / "src.mp4", dur=2.0, color="black")
    res = SubtitleStyleTool().run(
        work_dir=work_dir,
        upload_paths=upload_paths,
        params={"enabled": True, "font_size": 48, "color": "white",
                "position": "bottom", "shadow": True,
                "lines": ["hello"], "duration_s": 2.0,
                "source_video": src},
    )
    assert res.ok, res.message
    assert res.output_path and res.output_path.exists()
    assert res.output_path.read_bytes()[4:8] == b"ftyp"


def test_subtitle_skipped_when_disabled(work_dir, upload_paths):
    res = SubtitleStyleTool().run(
        work_dir=work_dir,
        upload_paths=upload_paths,
        params={"enabled": False},
    )
    assert res.ok and "skipped" in res.message


def test_subtitle_needs_source_and_lines(work_dir, upload_paths):
    res = SubtitleStyleTool().run(
        work_dir=work_dir,
        upload_paths=upload_paths,
        params={"enabled": True, "lines": ["x"]},  # 缺 source_video
    )
    assert not res.ok
