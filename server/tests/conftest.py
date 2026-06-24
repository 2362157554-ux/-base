"""pytest 配置：让 ``import app.*`` 在 ``server/`` 目录下可用。"""
import sys
from pathlib import Path

# 把 server/ 加进 sys.path，使 ``import app.foo`` 能工作
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import pytest


@pytest.fixture
def work_dir(tmp_path):
    """每个测试一个干净的工作目录。"""
    d = tmp_path / "work"
    d.mkdir()
    return d


@pytest.fixture
def upload_paths(tmp_path):
    """空的 upload_paths dict（很多 tool 容忍空 dict）。"""
    return {}


@pytest.fixture
def make_test_mp4(tmp_path):
    """工厂 fixture：调一次产一段 mp4，路径由调用者传。"""
    import subprocess

    def _make(path: Path, dur: float = 2.0, color: str = "red") -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", f"color=c={color}:s=320x240:d={dur}",
            "-pix_fmt", "yuv420p", str(path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return path

    return _make
