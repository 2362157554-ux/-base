# 快速跑通

## 0. 环境

| 工具 | 版本 | 备注 |
|---|---|---|
| Node.js | 20+ | 前端 |
| Python | 3.10+ | 后端 |
| ffmpeg | 任意 5.x+ | 路径 B 必需；Windows 可 `winget install Gyan.FFmpeg` |
| 剪映 6+ | — | 路径 A 必需（仅 Windows / macOS） |
| pytest | 7+ | 仅跑测试时需要 |

## 1. 启动后端

```bash
cd server
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

打开 http://localhost:8000/api/health 看到 `{"ok":true,...}` 即后端就绪。

## 2. 启动前端

```bash
cd web
npm install
npm run dev
```

打开 http://localhost:5173 。前端通过 Vite proxy 把 `/api/*` 转发给后端。

## 3. 一句话出片

1. 在右侧输入一句话（多行会自动拆成多段字幕）
2. （可选）左侧上传视频/音频
3. 选一条出片路径：剪映草稿 zip 或 ffmpeg 直出 MP4
4. 点「生成」→ 拿到产物下载链接

能力面板里的"字幕样式 / 拼接 / 转场 / 调色"开关打开后会被传给后端，
按 **上游 → 基线 → 后处理** 三阶段链式执行（详见 [CAPABILITIES.md](./CAPABILITIES.md)）。

## 4. Remotion Studio（可选）

```bash
cd web
npm run remotion:studio
```

打开 http://localhost:3000 可视化编辑 `BaseClip` 模板。

## 5. 测试

### 5.1 单元测试（推荐）

```bash
cd server
pip install pytest
python -m pytest tests/ -v
```

应输出 `17 passed`，覆盖：

- `tests/test_base_tool.py` — BaseTool 抽象结构
- `tests/test_registry.py` — 注册表 register / get_tool / list_tools
- `tests/test_tools_concat.py` — concat filter / demuxer / 跳过逻辑
- `tests/test_tools_color.py` — eq 调色 / 跳过 / 缺源报错
- `tests/test_tools_subtitle.py` — drawtext 烧录 / 跳过 / 缺源报错

> 需要本机有 ffmpeg；缺则相关 case 会 `SKIPPED`，不会 FAIL。

### 5.2 离线单元（不开 uvicorn）

```bash
cd server
python -m smoke_test
```

验证 draft JSON roundtrip + zip 打包。

### 5.3 端到端（需 uvicorn 在跑）

```bash
cd server
python e2e_smoke.py
```

预期输出（节选）：

```
=== POST /api/generate (prefer_path=draft) ===
200 {"job_id": "...", "path": "draft", ...}
=== POST /api/generate (prefer_path=ffmpeg) ===
200 {"job_id": "...", "path": "ffmpeg", ...}
ALL OK
```

## 6. 常见问题

| 现象 | 处理 |
|---|---|
| 后端起不来：`Form data requires python-multipart` | `pip install python-multipart` |
| `/api/health` 返回 `ffmpeg_available: false` | 装 ffmpeg 并加到 PATH |
| 前端打开是空白页 | 检查 Vite 是否启动、控制台 404 |
| 剪映打不开 draft zip | 路径 A 需剪映 6+，且只在 Win/macOS 工作 |
| 字幕烧录报"drawtext fontfile"错 | 仓库默认走 Noto CJK / 微软雅黑，Linux 需手动装 |
