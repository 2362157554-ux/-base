"""把 DraftScript 打成剪映可识别的 zip。

本模块是"草稿 JSON 序列化 + 文件打包"这一层独立逻辑的归宿，
不依赖 FastAPI / 路由层，方便测试和其它 caller 复用。

zip 结构（剪映客户端公开约定）：

    <draft_name>/
        draft_content.json     # 时间轴主文件
        draft.meta_info        # 元数据
"""
from __future__ import annotations

import copy
import io
import json
import zipfile
from pathlib import Path

from .schema import DraftScript


def to_json_bytes(obj: object) -> bytes:
    """统一序列化：UTF-8 + 缩进 + 中文不转义。"""
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")


def _cover_bytes(width: int, height: int) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (max(width, 1), max(height, 1)), (8, 10, 16)).save(
        buf,
        format="JPEG",
        quality=82,
    )
    return buf.getvalue()


def _copy_media_into_zip(
    z: zipfile.ZipFile,
    *,
    script: DraftScript,
    draft_root: str,
    storage_root: Path,
) -> None:
    used_names: set[str] = set()
    for material in script.materials.values():
        if material.local_path.startswith(("text://", "placeholder://")):
            continue
        source = Path(material.local_path)
        if not source.is_absolute():
            source = storage_root / source
        if not source.is_file():
            continue

        name = source.name
        if name in used_names:
            name = f"{material.material_id}_{name}"
        used_names.add(name)
        archive_path = f"materials/{name}"
        z.write(source, f"{draft_root}/{archive_path}")
        material.local_path = archive_path


def zip_draft(
    script: DraftScript,
    *,
    storage_root: str | Path | None = None,
    include_media: bool = False,
) -> bytes:
    """把 DraftScript 打成用户下载的 zip 字节流。"""
    packed = copy.deepcopy(script) if include_media else script
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        if include_media and storage_root is not None:
            _copy_media_into_zip(
                z,
                script=packed,
                draft_root=packed.name,
                storage_root=Path(storage_root),
            )
        # draft_content.json
        z.writestr(f"{packed.name}/draft_content.json", to_json_bytes(packed.to_json()))
        # draft.meta_info（剪映需要此文件存在）
        meta = {
            "draft_id": packed.draft_id,
            "draft_name": packed.name,
            "create_time": packed.create_time,
            "tm_draft_cloud_cover": "",
            "draft_cover": "draft_cover.jpg",
            "draft_root_path": packed.name,
            "tm_draft_create_time": packed.create_time,
        }
        z.writestr(f"{packed.name}/draft.meta_info", to_json_bytes(meta))
        z.writestr(f"{packed.name}/draft_cover.jpg", _cover_bytes(packed.width, packed.height))
    return buf.getvalue()


def inspect_draft_zip(blob: bytes) -> dict:
    """Return a structural report for a generated draft zip."""
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = set(z.namelist())
        content_names = [name for name in names if name.endswith("/draft_content.json")]
        meta_names = [name for name in names if name.endswith("/draft.meta_info")]
        cover_names = [name for name in names if name.endswith("/draft_cover.jpg")]
        missing_media: list[str] = []

        if content_names:
            root = content_names[0].rsplit("/", 1)[0]
            content = json.loads(z.read(content_names[0]))
            materials = content.get("materials", {})
            for group in ("videos", "audios", "stickers"):
                for material in materials.get(group, []):
                    path = str(material.get("path", ""))
                    if not path or path.startswith(("placeholder://", "text://")):
                        continue
                    if f"{root}/{path}" not in names:
                        missing_media.append(path)

    ok = bool(content_names and meta_names and cover_names) and not missing_media
    return {
        "ok": ok,
        "has_draft_content": bool(content_names),
        "has_meta": bool(meta_names),
        "has_cover": bool(cover_names),
        "missing_media": missing_media,
        "entries": sorted(names),
    }


__all__ = ["inspect_draft_zip", "to_json_bytes", "zip_draft"]
