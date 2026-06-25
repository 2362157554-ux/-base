"""transition tool tests."""
import shutil

import pytest

from app.tools.transition import TransitionTool


pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe unavailable",
)


def test_transition_xfade_two_videos(work_dir, upload_paths, make_test_mp4):
    a = make_test_mp4(work_dir / "a.mp4", dur=1.0, color="red")
    b = make_test_mp4(work_dir / "b.mp4", dur=1.0, color="blue")
    upload_paths["/api/files/a.mp4"] = a
    upload_paths["/api/files/b.mp4"] = b

    res = TransitionTool().run(
        work_dir=work_dir,
        upload_paths=upload_paths,
        params={
            "enabled": True,
            "videos": ["/api/files/a.mp4", "/api/files/b.mp4"],
            "kind": "fade",
            "duration_s": 0.2,
        },
    )

    assert res.ok, res.message
    assert res.output_path
    assert res.output_path.read_bytes()[4:8] == b"ftyp"
