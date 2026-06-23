# -base / 一句话剪辑

> 输入一句话文案 + 几个素材 → 自动生成可发布的短视频（MP4）。

本仓库用 **Remotion + 自研 FastAPI 后端 + ffmpeg / 剪映双出片路径** 把"一句话"变成视频。
代码全部为本项目作者重写，思路参考 [pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft) 与
[Remotion](https://github.com/remotion-dev/remotion)，详见 [THIRD_PARTY_LICENSES.md](./THIRD_PARTY_LICENSES.md)。

## 架构

```
                ┌──────────────────────────────────────────────┐
                │             web/  (React + Vite)             │
                │  - 一句话输入框、素材上传                     │
                │  - Remotion Player 预览                     │
                │  - Remotion renderMedia 离线导出 PNG/片段    │
                └────────────────────┬─────────────────────────┘
                                     │ POST /api/jobs
                                     ▼
                ┌──────────────────────────────────────────────┐
                │          server/  (FastAPI, Python)          │
                │                                              │
                │  ┌─────────────┐    ┌─────────────────────┐  │
                │  │ DraftGen    │ -> │ 生成剪映 draft_content.json │
                │  └─────────────┘    └─────────────────────┘  │
                │                                              │
                │  ┌─────────────┐    ┌─────────────────────┐  │
                │  │ FfmpegMux   │ -> │ 兜底合成 MP4       │  │
                │  └─────────────┘    └─────────────────────┘  │
                └────────────────────┬─────────────────────────┘
                                     │
              ┌──────────────────────┴───────────────────────┐
              ▼                                              ▼
       路径 A：返回 .draft zip                       路径 B：返回 MP4
       （用户在自己电脑用剪映一键导出）              （服务端 ffmpeg 直接出片）
```

## 目录

```
-base/
├── web/                       # React + Vite + Remotion
│   ├── src/
│   │   ├── components/        # 编辑器 UI
│   │   └── remotion/          # Remotion 组合（字幕条/贴纸/过渡）
│   └── package.json
├── server/                    # FastAPI
│   └── app/
│       ├── api/               # 路由
│       ├── draft/             # 剪映草稿 JSON 生成器（自研）
│       └── render/            # ffmpeg 兜底合成
├── docs/                      # 设计文档、schema 笔记
├── THIRD_PARTY_LICENSES.md
└── README.md
```

## 跑起来

### 0. 前置环境

- Node.js 20+
- Python 3.10+
- ffmpeg（路径 B 必需；Windows 可用 `winget install Gyan.FFmpeg`）
- 剪映 6+（路径 A 必需）

### 1. 后端

```bash
cd server
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. 前端

```bash
cd web
npm install
npm run dev                     # http://localhost:5173
```

### 3. 一句话出片

1. 打开 http://localhost:5173
2. 输入文案、上传几张素材、选一个模板
3. 点「生成」→ 后端返回两种产物之一：
   - `*.draft.zip`：下载 → 解压到剪映草稿目录 → 在剪映里点「导出」
   - `out.mp4`：直接拿到成片

## 双出片路径的取舍

| 维度 | 路径 A：剪映草稿 | 路径 B：ffmpeg 兜底 |
|---|---|---|
| 依赖 | 必须本地有剪映 | 纯服务端 |
| 转场/特效 | 用剪映原生素材库 | 仅基础转场 + 字幕 |
| 速度 | 慢（要手动点） | 快（全自动） |
| 默认 | 当剪映可用时优先 | 兜底 |

## 路线图

- [x] 仓库骨架 + 双路径设计
- [x] Remotion 端：一个「字幕条 + 贴纸 + 渐入」组合（自研 `BaseClip`）
- [x] server.draft：生成合法 `draft_content.json`，打成 zip
- [x] server.render：ffmpeg 把视频 + BGM + 字幕烧录合成 MP4
- [x] 端到端跑通：`python e2e_smoke.py` 全绿

详细步骤见 [docs/RUN.md](./docs/RUN.md)。

## 法律与版权

详见 [THIRD_PARTY_LICENSES.md](./THIRD_PARTY_LICENSES.md)。简言之：本仓库不复制
上游代码，所有功能为重写实现。
