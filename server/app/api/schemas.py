"""请求/响应模型（pydantic）。"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ClipItem(BaseModel):
    """一个素材描述（来自前端的 payload）。"""

    kind: Literal["video", "audio", "text", "sticker"]
    url: str | None = Field(default=None, description="对 video/audio：已上传文件的相对 URL")
    content: str | None = Field(default=None, description="对 text：文字内容")
    duration_s: float | None = Field(default=None, description="视频/音频素材的原始时长（秒），text 可省")
    width: int | None = None
    height: int | None = None


class GenerateRequest(BaseModel):
    """生成任务请求。"""

    text: str = Field(..., min_length=1, max_length=500, description="一句话文案")
    clips: list[ClipItem] = Field(default_factory=list, description="素材列表")
    width: int = 1080
    height: int = 1920
    fps: int = 30
    total_duration_s: float = Field(default=6.0, ge=1.0, le=120.0)
    prefer_path: Literal["draft", "ffmpeg"] = "draft"
    bpm: float | None = Field(default=None, description="如配 BGM 可选")

    # BaseTool 链参数：key 是工具名，value 是该工具的 params dict
    # 例：{"subtitle": {"enabled": True, "font_size": 56}}
    tools: dict[str, dict] | None = Field(default=None, description="BaseTool 参数覆盖")


class GenerateResponse(BaseModel):
    job_id: str
    path: Literal["draft", "ffmpeg"]
    artifact_url: str
    message: str = ""


class HealthResponse(BaseModel):
    ok: bool = True
    ffmpeg_available: bool
    time: float
