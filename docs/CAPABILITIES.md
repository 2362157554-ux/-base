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

## 新增能力（3 步）

1. `server/app/tools/your_tool.py`：`class X(BaseTool)`，写 `params_schema` 和 `run`
2. `server/app/tools/registry.py`：`register(X())` 一行
3. 前端不动 —— `CapabilitiesPanel` 自动从 `/api/tools` 拉 schema 渲染

## 原则

零新依赖（只调 ffmpeg 子进程）、零大内存（不引入 ML 模型）、零下载（不打包字体/素材）。