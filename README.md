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
                │  - 能力面板（CapabilitiesPanel，schema 驱动） │
                │  - Remotion Player 预览                       │
                └────────────────────┬─────────────────────────┘
                                     │ GET /api/tools 拉 schema
                                     │ POST /api/generate 带 tools{}
                                     ▼
                ┌──────────────────────────────────────────────┐
                │          server/  (FastAPI, Python)          │
                │                                              │
                │  ┌────────────────────────┐  ┌─────────────┐  │
                │  │ server/app/draft/      │  │ server/app/ │  │
                │  │   schema.py 时间轴模型 │  │ render/     │  │
                │  │   packaging.py 打包zip │  │   ffmpeg.py │  │
                │  └────────────────────────┘  └─────────────┘  │
                │                                              │
                │  ┌──────────────────────────────────────────┐ │
                │  │ server/app/tools/  (BaseTool 架构)      │ │
                │  │   compose / subtitle / concat /          │ │
                │  │   transition / color  → 链式执行        │ │
                │  └──────────────────────────────────────────┘ │
                └────────────────────┬─────────────────────────┘
                                     │
              ┌──────────────────────┴───────────────────────┐
              ▼                                              ▼
       路径 A：返回 .draft zip                       路径 B：返回 MP4
       （用户在自己电脑用剪映一键导出）              （服务端 ffmpeg 直接出片）
```

**出片调用链**：上游 tool（concat / transition，从用户素材）→ 基线 compose（永远跑）
→ 后处理 tool（color / subtitle，链式叠加）。详见 [docs/CAPABILITIES.md](./docs/CAPABILITIES.md)。

## 目录

```
-base/
├── web/                       # React + Vite + Remotion
│   └── src/
│       ├── App.tsx            # 编辑器主组件
│       ├── api.ts             # 后端 API 客户端
│       ├── tools/             # 能力面板（schema 驱动）
│       └── remotion/          # Remotion 组合（字幕条/贴纸/过渡）
├── server/                    # FastAPI
│   ├── app/
│   │   ├── api/               # 路由
│   │   ├── draft/             # 剪映草稿 JSON 生成器（自研）
│   │   │   ├── schema.py      #   时间轴数据模型
│   │   │   └── packaging.py   #   打 zip
│   │   ├── render/            # ffmpeg 兜底合成
│   │   └── tools/             # BaseTool 架构 + 5 个 tool
│   │       ├── base.py        #   抽象类
│   │       ├── registry.py    #   注册表
│   │       ├── compose.py     #   主出片
│   │       ├── subtitle.py    #   字幕样式
│   │       ├── concat.py      #   拼接
│   │       ├── transition.py  #   转场
│   │       └── color.py       #   调色
│   ├── tests/                 # pytest 单测（17 cases）
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── smoke_test.py          # 离线单元
│   └── e2e_smoke.py           # 端到端（需 uvicorn 在跑）
├── docs/                      # 设计文档
│   ├── ARCHITECTURE.md        #   架构与设计取舍
│   ├── CAPABILITIES.md        #   能力清单 + 新增流程
│   └── RUN.md                 #   跑通 + 测试
├── .github/workflows/         # CI
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
- [x] **BaseTool 架构**：所有 ffmpeg-only 能力以 `BaseTool` 子类形式挂到注册表
- [x] **拼接 / 转场 / 调色 / 字幕样式** 四个工具上线（详见 [docs/CAPABILITIES.md](./docs/CAPABILITIES.md)）
- [x] 前端能力面板：schema 驱动，新 tool 自动出现
- [x] **`server/tests/` + pytest**：17 个 case 覆盖 BaseTool / 注册表 / 三个 tool 的真实 ffmpeg 调用
- [x] **`draft/packaging.py` 重构**：`_zip_draft` 从 routes 挪到独立模块，可复用 + 可测
- [x] **CI**：`.github/workflows/ci.yml` 跑 pytest 守住新 tool 加入时不出错
- [x] **`docs/RUN.md` 同步**：补 BaseTool 章节 + pytest 使用说明

## 测试

```bash
cd server
pip install pytest
python -m pytest tests/ -v        # 17 passed
python -m smoke_test              # 离线单元
python e2e_smoke.py               # 需 uvicorn 先起
```

短期不再追新功能；下一阶段候选：缩略图（`thumbnail`）、片头片尾（`intro_outro`），
按需手动注册即可，不破坏现有架构。详细步骤见 [docs/RUN.md](./docs/RUN.md)。

## 法律与版权

详见 [THIRD_PARTY_LICENSES.md](./THIRD_PARTY_LICENSES.md)。简言之：本仓库不复制
上游代码，所有功能为重写实现。
