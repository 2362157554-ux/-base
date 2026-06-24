# 能力清单（CAPABILITIES）

> 所有 ffmpeg-only 能力由 `BaseTool` 架构承载。新增能力 = 一个 `BaseTool` 子类 + `register()` 一行。

## 已注册

| 工具 | 行为 | ffmpeg 思路 |
|---|---|---|
| `compose` | 基线出片（视频+字幕+BGM→MP4） | `compose_from_script`：drawtext + amix |
| `subtitle` | 字幕样式（颜色/字号/位置/阴影） | `drawtext`，自动选 Noto CJK / 微软雅黑 |
| `concat` | 多段拼接 | `concat` filter（不同分辨率也行）或 demuxer |
| `transition` | 两段视频加转场 | `xfade`（fade/wipe/slide 等 7 种） |
| `color` | 调亮度/对比度/饱和度 | `eq` filter |

## 调用链

```
上游（可选）：concat, transition      ← 直接吃用户素材
基线（永远）：compose                 ← 出基线 MP4
后处理（可选）：color, subtitle      ← 链式叠加，拿上一个 output
```

## 调用示例（curl）

发现所有能力 + schema：

```bash
curl -s http://localhost:8000/api/tools | python -m json.tool
```

节选（`subtitle`）：

```json
{
  "name": "subtitle",
  "display_name": "字幕样式",
  "summary": "把字幕烧录成可定制的样式（颜色/字号/位置/阴影）。",
  "requires_ffmpeg": true,
  "params": [
    {"key": "enabled", "label": "启用", "type": "bool", "default": true, ...},
    {"key": "font_size", "label": "字号", "type": "int", "default": 56, "min": 16, "max": 160, ...},
    {"key": "color", "label": "字色", "type": "choice", "default": "white",
     "choices": ["white", "yellow", "black", "red"], ...},
    {"key": "position", "label": "位置", "type": "choice", "default": "bottom",
     "choices": ["bottom", "middle", "top"], ...},
    {"key": "shadow", "label": "加阴影", "type": "bool", "default": true, ...}
  ]
}
```

启用字幕 + 调色（一次出片）：

```bash
curl -s -X POST http://localhost:8000/api/generate \
  -H "content-type: application/json" \
  -d '{
    "text": "第一行\n第二行",
    "clips": [],
    "width": 720, "height": 1280, "fps": 30,
    "total_duration_s": 4.0,
    "prefer_path": "ffmpeg",
    "tools": {
      "subtitle": {"enabled": true, "font_size": 56, "color": "yellow", "shadow": true},
      "color":    {"enabled": true, "brightness": 0.05, "contrast": 1.15, "saturation": 1.2}
    }
  }'
```

响应里的 `message` 会列出实际跑过的 tool，便于确认链路：

```
ffmpeg 直接合成的 MP4（tools: color, subtitle）
```

## 新增能力（3 步）

1. `server/app/tools/your_tool.py`：`class X(BaseTool)`，写 `params_schema` 和 `run`
2. `server/app/tools/registry.py`：`register(X())` 一行
3. 前端不动 —— `CapabilitiesPanel` 自动从 `/api/tools` 拉 schema 渲染

新 tool 写完后跑一次 `pytest server/tests/ -v`，17 个 case 仍是绿的就说明没破坏现有链路。

## 原则

零新依赖（只调 ffmpeg 子进程）、零大内存（不引入 ML 模型）、零下载（不打包字体/素材）。
