"""BaseTool：所有 ffmpeg-only 剪辑能力的统一抽象。"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ParamType(str, Enum):
    BOOL = "bool"; INT = "int"; FLOAT = "float"
    TEXT = "text"; CHOICE = "choice"; FILE = "file"


@dataclass(frozen=True)
class ParamSpec:
    key: str; label: str; type: ParamType
    default: Any = None
    choices: tuple = ()
    min: float | None = None
    max: float | None = None
    help: str = ""


@dataclass
class ToolResult:
    ok: bool
    output_path: Path | None = None
    artifact_url: str | None = None
    message: str = ""
    data: dict = field(default_factory=dict)


class BaseTool(ABC):
    name = ""; display_name = ""; summary = ""
    requires_ffmpeg: bool = True
    min_video_inputs: int = 0
    max_video_inputs: int | None = None

    @abstractmethod
    def params_schema(self) -> list[ParamSpec]: ...

    @abstractmethod
    def run(self, *, work_dir: Path,
            upload_paths: dict, params: dict) -> ToolResult: ...
