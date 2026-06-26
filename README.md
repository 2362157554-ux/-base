# -base / 一句话剪辑

> 输入一句话文案 + 几个素材 → 自动生成可发布的短视频（MP4）。

本仓库用 **Remotion + 自研 FastAPI 后端 + ffmpeg / 剪映草稿** 把"一句话"变成视频。
代码全部为本项目作者重写，思路参考 [pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft) 与
[Remotion](https://github.com/remotion-dev/remotion)，详见 [THIRD_PARTY_LICENSES.md](./THIRD_PARTY_LICENSES.md)。

## 设计语言

本仓库借鉴 `awesome-design-md` 的做法，在根目录新增 [DESIGN.md](./DESIGN.md) 作为 UI 设计契约。
后续让 AI 或人工继续改前端时，优先遵守其中的暗色剪辑工作台、真实预览优先、紧凑控制面板、
hairline 边框和单一主行动色规则。

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
              ┌──────────────────────┼───────────────────────┐
              ▼                      ▼                       ▼
       路径 A：.draft zip      路径 B：ffmpeg MP4      路径 C：Remotion MP4
       （剪映打开导出）        （服务端兜底合成）       （复用 web/ 组合渲染）
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
│   │   ├── render/            # ffmpeg 兜底合成 + Remotion CLI 桥接
│   │   └── tools/             # BaseTool 架构 + 5 个 tool
│   │       ├── base.py        #   抽象类
│   │       ├── registry.py    #   注册表
│   │       ├── compose.py     #   主出片
│   │       ├── subtitle.py    #   字幕样式
│   │       ├── concat.py      #   拼接
│   │       ├── transition.py  #   转场
│   │       └── color.py       #   调色
│   ├── tests/                 # pytest 单测（23 cases）
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── smoke_test.py          # 离线单元
│   └── e2e_smoke.py           # 端到端（需 uvicorn 在跑）
├── docs/                      # 设计文档
│   ├── ARCHITECTURE.md        #   架构与设计取舍
│   ├── CAPABILITIES.md        #   能力清单 + 新增流程
│   └── RUN.md                 #   跑通 + 测试
├── .github/workflows/         # CI
├── DESIGN.md                  # UI 视觉语言与 AI 设计约束
├── THIRD_PARTY_LICENSES.md
└── README.md
```

## 跑起来

### 0. 前置环境

- Node.js 20.19+（或 22.12+）
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
2. 输入文案、上传几张素材、选择出片路径
3. 点「生成」→ 后端返回产物：
   - `*.draft.zip`：包含草稿 JSON、封面和已上传素材；下载 → 解压到剪映草稿目录 → 在剪映里点「导出」
   - `*.mp4`：ffmpeg 或 Remotion 直接生成的成片

## 三条出片路径的取舍

| 维度 | 路径 A：剪映草稿 | 路径 B：ffmpeg 兜底 | 路径 C：Remotion |
|---|---|---|---|
| 依赖 | 用户本地剪映 | 服务端 ffmpeg | 服务端 Node + web 依赖 |
| 转场/特效 | 后续由剪映增强 | 基础转场 + 字幕 | 复用 `web/src/remotion` 组合 |
| 速度 | 慢（要手动点） | 快（全自动） | 中等，首次会下载/启动浏览器 |
| 适合 | 需要进剪映二次编辑 | 稳定兜底出片 | 预览和成片视觉一致 |

## 路线图

- [x] 仓库骨架 + 三路径设计
- [x] Remotion 端：一个「字幕条 + 贴纸 + 渐入」组合（自研 `BaseClip`）
- [x] server.draft：生成合法 `draft_content.json`，打成 zip
- [x] server.render：ffmpeg 把视频 + BGM + 字幕烧录合成 MP4
- [x] server.render：Remotion CLI 复用 `BaseClip` 直接渲染 MP4
- [x] 剪映草稿 zip：打包素材、封面，并提供 `/api/outputs/{name}/inspect` 结构检查
- [x] 端到端跑通：`python e2e_smoke.py` 全绿
- [x] **BaseTool 架构**：所有 ffmpeg-only 能力以 `BaseTool` 子类形式挂到注册表
- [x] **拼接 / 转场 / 调色 / 字幕样式** 四个工具上线（详见 [docs/CAPABILITIES.md](./docs/CAPABILITIES.md)）
- [x] 前端能力面板：schema 驱动，新 tool 自动出现
- [x] **`server/tests/` + pytest**：23 个 case 覆盖 API 字段契约 / BaseTool / 注册表 / draft 打包 / Remotion 命令 / 四个 tool 的真实 ffmpeg 调用
- [x] **`draft/packaging.py` 重构**：`_zip_draft` 从 routes 挪到独立模块，可复用 + 可测
- [x] **CI**：`.github/workflows/ci.yml` 跑后端 pytest、前端 audit 和 build
- [x] **`docs/RUN.md` 同步**：补 BaseTool 章节 + pytest 使用说明

## 测试

```bash
cd server
pip install pytest
python -m pytest tests/ -v        # 23 passed
npm --prefix ../web run build     # 前端类型检查 + Vite 构建
python -m smoke_test              # 离线单元
python e2e_smoke.py               # 需 uvicorn 先起
```

短期不再追新功能；下一阶段候选：缩略图（`thumbnail`）、片头片尾（`intro_outro`），
按需手动注册即可，不破坏现有架构。详细步骤见 [docs/RUN.md](./docs/RUN.md)。

## 法律与版权

详见 [THIRD_PARTY_LICENSES.md](./THIRD_PARTY_LICENSES.md)。简言之：本仓库不复制
上游代码，所有功能为重写实现。
