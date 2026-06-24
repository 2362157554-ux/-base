"""把 DraftScript 打成剪映可识别的 zip。

本模块是"草稿 JSON 序列化 + 文件打包"这一层独立逻辑的归宿，
不依赖 FastAPI / 路由层，方便测试和其它 caller 复用。

zip 结构（剪映客户端公开约定）：

    <draft_name>/
        draft_content.json     # 时间轴主文件
        draft.meta_info        # 元数据
"""
from __future__ import annotations

import io
import json
import zipfile

from .schema import DraftScript


def to_json_bytes(obj: object) -> bytes:
    """统一序列化：UTF-8 + 缩进 + 中文不转义。"""
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")


def zip_draft(script: DraftScript) -> bytes:
    """把 DraftScript 打成用户下载的 zip 字节流。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # draft_content.json
        z.writestr(f"{script.name}/draft_content.json", to_json_bytes(script.to_json()))
        # draft.meta_info（剪映需要此文件存在）
        meta = {
            "draft_id": script.draft_id,
            "draft_name": script.name,
            "create_time": script.create_time,
            "tm_draft_cloud_cover": "",
            "draft_cover": "draft_cover.jpg",
            "draft_root_path": script.name,
            "tm_draft_create_time": script.create_time,
        }
        z.writestr(f"{script.name}/draft.meta_info", to_json_bytes(meta))
    return buf.getvalue()


__all__ = ["to_json_bytes", "zip_draft"]
