"""color tool 测试：用 lavfi 造一段 mp4 → eq filter 调色。"""
import shutil

import pytest

from app.tools.color import ColorTool


pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg unavailable"
)


def test_color_grades_a_video(work_dir, upload_paths, make_test_mp4):
    src = make_test_mp4(work_dir / "src.mp4", dur=1.0, color="red")
    res = ColorTool().run(
        work_dir=work_dir,
        upload_paths=upload_paths,
        params={"enabled": True, "brightness": 0.1,
                "contrast": 1.2, "saturation": 1.1,
                "source_video": src},
    )
    assert res.ok, res.message
    assert res.output_path and res.output_path.exists()
    assert res.output_path.read_bytes()[4:8] == b"ftyp"


def test_color_skipped_by_default(work_dir, upload_paths, make_test_mp4):
    src = make_test_mp4(work_dir / "src.mp4", dur=1.0, color="red")
    res = ColorTool().run(
        work_dir=work_dir,
        upload_paths=upload_paths,
        params={"enabled": False, "source_video": src},
    )
    assert res.ok and "skipped" in res.message


def test_color_needs_source(work_dir, upload_paths):
    res = ColorTool().run(
        work_dir=work_dir,
        upload_paths=upload_paths,
        params={"enabled": True},
    )
    assert not res.ok
