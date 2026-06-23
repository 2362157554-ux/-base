"""FastAPI 应用主入口。"""
from __future__ import annotations

import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="-base / 一句话剪辑",
        version="0.1.0",
        description="把一句话文案 + 几个素材变成可发布短视频。",
    )

    # 允许本地前端跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api")

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": "-base",
            "description": "一句话剪辑",
            "docs": "/docs",
            "started_at": str(int(time.time())),
        }

    return app


app = create_app()
