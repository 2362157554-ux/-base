# 架构笔记

## 设计目标

1. 用户在网页输入一句话 + 几个素材 → 拿到一段 MP4。
2. 出片要稳：剪映草稿便于二次编辑，ffmpeg 负责兜底直出，Remotion 负责视觉一致的直出。
3. 代码全部自有，思路借鉴但不抄袭上游。

## 为什么不用 pyJianYingDraft 直接 vendor

| 方式 | 风险 | 可维护性 |
|---|---|---|
| 直接复制源码（vendor） | 需要原样保留 LICENSE + NOTICE，否则违反 MIT | 跟随上游更新成本低，但代码不是自己的 |
| 重写 + 借鉴 schema | 需要"读后自己写"，不能大段复制 | 完全自主演进，**本项目采用此方案** |

## 自研 schema（不复制 pyJianYingDraft 的代码）

剪映草稿目录由一组固定文件组成，**这是公开约定**（剪映客户端格式），任何人都能生成：

```
Drafts/<draft_name>/
├── draft.meta_info          # 草稿元数据（封面、时长）
├── draft_content.json       # 时间轴主文件
└── draft_cover.jpg          # 缩略图
```

我们只用 `draft_content.json` 的公开字段约定，**字段含义和层级关系**借鉴自上游文档
和剪映客户端逆向资料，但 JSON 的字段值由本项目代码生成。

## 时间区间约定

pyJianYingDraft 用「持续时长语义」（`trange("0s", "5s")` 表示从 0s 起持续 5s）。
我们采用相同语义以减少认知负担，但实现是独立的：

```
[target_start, target_start + duration)   ← target 区段（在时间轴上的位置）
[source_start, source_start + duration)   ← source 区段（从素材里取哪段）
```

## 渲染流水线（三路径）

### 路径 A：剪映草稿
1. server.draft 根据 web 上传的素材 + 文案生成 `draft_content.json`
2. 打包成 zip 让用户下载，zip 中包含草稿 JSON、封面和已上传素材
3. 用户解压到剪映草稿目录 → 剪映打开批量导出

### 路径 B：ffmpeg 兜底
1. server.render 根据 DraftScript 直接构造 ffmpeg filter graph
2. 基线 `compose` 生成 MP4；`concat` / `transition` 可先产出主视频，`color` / `subtitle` 可后处理

### 路径 C：Remotion
1. web/Remotion 注册 `BaseClip` 组合，并提供浏览器 Player 预览
2. server.render.remotion 写入 props JSON
3. 后端调用 `web/` 下的 Remotion CLI 渲染 MP4，再复制到 `server/storage/outputs`

## 模块边界

- `server/app/draft/` —— 纯 JSON 生成，**不调剪映进程**，跨平台
- `server/app/render/` —— ffmpeg 合成与 Remotion CLI 桥接，**不依赖剪映**
- `web/src/remotion/` —— 视觉/动效，既供浏览器预览，也供 Remotion CLI 渲染
- `web/src/components/` —— 编辑器 UI + 与后端通信

任何模块都不应该跨边界去调别的模块的内部 API，**只用 HTTP/文件**。
