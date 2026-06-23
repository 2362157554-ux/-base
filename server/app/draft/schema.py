"""剪映草稿 schema（自研实现）。

剪映草稿本质是一组固定 JSON 文件。本模块只关心
``draft_content.json`` 的时间轴结构——这是剪映客户端公开约定。

字段语义参考剪映客户端逆向资料与 pyJianYingDraft 文档，
但所有 Python 类型定义、命名、序列化逻辑均为本项目作者原创。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any
import uuid


# ---------------------------------------------------------------------------
# 枚举
# ---------------------------------------------------------------------------


class TrackKind(str, Enum):
    """时间轴上的轨道类型。"""

    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    STICKER = "sticker"
    EFFECT = "effect"


class MaterialKind(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    STICKER = "sticker"


# ---------------------------------------------------------------------------
# 时间区间
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Timerange:
    """时间区间（左闭右开），持续时长语义。

    与上游 ``trange("0s", "5s")`` 语义一致——但实现为本项目自有。
    """

    start_us: int          # 起始微秒（相对轨道起点）
    duration_us: int       # 持续微秒

    @property
    def end_us(self) -> int:
        return self.start_us + self.duration_us

    def to_dict(self) -> dict[str, int]:
        return {
            "start": self.start_us,
            "duration": self.duration_us,
        }

    @classmethod
    def from_seconds(cls, start_s: float, duration_s: float) -> "Timerange":
        return cls(
            start_us=int(round(start_s * 1_000_000)),
            duration_us=int(round(duration_s * 1_000_000)),
        )


# ---------------------------------------------------------------------------
# 素材
# ---------------------------------------------------------------------------


@dataclass
class Material:
    """轨道上的素材（视频/音频/文字/贴纸）。"""

    kind: MaterialKind
    local_path: str                  # 服务端存储的相对路径
    duration_us: int = 0             # 原始素材长度（微秒）
    width: int = 0
    height: int = 0
    material_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.material_id,
            "type": self.kind.value,
            "path": self.local_path,
            "duration": self.duration_us,
            "width": self.width,
            "height": self.height,
        }


@dataclass
class TextMaterial(Material):
    """文字素材（继承自 Material 但 content 字段专属）。"""

    local_path: str = ""
    content: str = ""
    font: str = "Source Han Sans"
    color: tuple[float, float, float] = (1.0, 1.0, 1.0)
    font_size: int = 48

    def __post_init__(self) -> None:
        if not self.local_path:
            # 文字素材没有真正的本地路径，用 id 占位
            self.local_path = f"text://{self.material_id}"

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "content": self.content,
                "font": self.font,
                "color": list(self.color),
                "font_size": self.font_size,
            }
        )
        return base


# ---------------------------------------------------------------------------
# 片段
# ---------------------------------------------------------------------------


@dataclass
class Segment:
    """轨道上的一个片段（对应素材在某段时间内的呈现）。"""

    material_id: str
    target: Timerange                # 在时间轴上的位置与时长
    source: Timerange                # 从素材里取哪一段
    speed: float = 1.0
    volume: float = 1.0              # 仅音频/视频有效
    intro_animation: str | None = None
    outro_animation: str | None = None
    segment_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.segment_id,
            "material_id": self.material_id,
            "target_timerange": self.target.to_dict(),
            "source_timerange": self.source.to_dict(),
            "speed": self.speed,
            "volume": self.volume,
            "intro_animation": self.intro_animation,
            "outro_animation": self.outro_animation,
        }


# ---------------------------------------------------------------------------
# 轨道
# ---------------------------------------------------------------------------


@dataclass
class Track:
    """一条时间轴轨道。"""

    kind: TrackKind
    segments: list[Segment] = field(default_factory=list)
    track_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])

    def add(self, segment: Segment) -> "Track":
        self.segments.append(segment)
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.track_id,
            "type": self.kind.value,
            "segments": [s.to_dict() for s in self.segments],
        }


# ---------------------------------------------------------------------------
# 草稿
# ---------------------------------------------------------------------------


@dataclass
class DraftScript:
    """一个完整的剪映草稿（自研 JSON 模型）。"""

    name: str
    width: int
    height: int
    fps: int
    tracks: list[Track] = field(default_factory=list)
    materials: dict[str, Material] = field(default_factory=dict)
    draft_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    create_time: int = 0            # unix seconds，由调用方填充

    # 工具方法 ------------------------------------------------------------

    def add_track(self, kind: TrackKind) -> Track:
        t = Track(kind=kind)
        self.tracks.append(t)
        return t

    def register_material(self, material: Material) -> None:
        self.materials[material.material_id] = material

    def add_segment_to(
        self,
        track_kind: TrackKind,
        material: Material,
        target: Timerange,
        *,
        source: Timerange | None = None,
        speed: float = 1.0,
        volume: float = 1.0,
        intro: str | None = None,
        outro: str | None = None,
    ) -> Segment:
        """便捷方法：注册素材 + 找到/创建轨道 + 追加片段。"""
        self.register_material(material)
        # 找到同类型轨道，没则建
        track = next((t for t in self.tracks if t.kind == track_kind), None)
        if track is None:
            track = self.add_track(track_kind)
        seg = Segment(
            material_id=material.material_id,
            target=target,
            source=source or Timerange(0, target.duration_us),
            speed=speed,
            volume=volume,
            intro_animation=intro,
            outro_animation=outro,
        )
        track.add(seg)
        return seg

    def total_duration_us(self) -> int:
        end = 0
        for t in self.tracks:
            for s in t.segments:
                end = max(end, s.target.end_us)
        return end

    # 序列化 --------------------------------------------------------------

    def to_json(self) -> dict[str, Any]:
        """生成 ``draft_content.json`` 顶层结构。"""
        return {
            "id": self.draft_id,
            "name": self.name,
            "canvas_config": {
                "width": self.width,
                "height": self.height,
                "fps": self.fps,
            },
            "tracks": [t.to_dict() for t in self.tracks],
            "materials": {
                "videos": [m.to_dict() for m in self.materials.values() if m.kind == MaterialKind.VIDEO],
                "audios": [m.to_dict() for m in self.materials.values() if m.kind == MaterialKind.AUDIO],
                "texts": [m.to_dict() for m in self.materials.values() if m.kind == MaterialKind.TEXT],
                "stickers": [m.to_dict() for m in self.materials.values() if m.kind == MaterialKind.STICKER],
            },
            "create_time": self.create_time,
            "total_duration_us": self.total_duration_us(),
        }
