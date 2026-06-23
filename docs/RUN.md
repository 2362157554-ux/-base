# 快速跑通

## 0. 环境

| 工具 | 版本 | 备注 |
|---|---|---|
| Node.js | 20+ | 前端 |
| Python | 3.10+ | 后端 |
| ffmpeg | 任意 5.x+ | 路径 B 必需；Windows 可 `winget install Gyan.FFmpeg` |
| 剪映 6+ | — | 路径 A 必需（仅 Windows / macOS） |

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

打开 http://localhost:5173 。前端通过 Vite proxy 把 `/api/*` 转给后端。

## 3. 一句话出片

1. 在右侧输入一句话（多行会拆成多段字幕）
2. （可选）左侧上传视频/音频
3. 选「出片路径」：剪映草稿 zip 或 ffmpeg 直出 MP4
4. 点「生成」→ 拿到产物下载链接

## 4. Remotion Studio（可选）

```bash
cd web
npm run remotion:studio
```

打开 http://localhost:3000 可视化编辑 `BaseClip` 模板。

## 5. 冒烟测试

不开 uvicorn 跑单元：

```bash
cd server
python -m smoke_test
```

开了 uvicorn 之后跑端到端：

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
