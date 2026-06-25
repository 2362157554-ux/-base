"""Remotion renderer command construction tests."""
from pathlib import Path

from app.render.remotion import build_remotion_command


def test_build_remotion_command_uses_project_entrypoint(tmp_path):
    web_root = tmp_path / "web"
    props = tmp_path / "props.json"
    output = tmp_path / "out.mp4"

    cmd = build_remotion_command(
        web_root=web_root,
        composition_id="base-clip",
        props_path=props,
        output_path=output,
    )

    joined = " ".join(str(part) for part in cmd)
    assert "remotion" in joined
    assert "src/remotion/index.ts" in joined.replace("\\", "/")
    assert "base-clip" in cmd
    assert str(props) in cmd
    assert str(output) in cmd
