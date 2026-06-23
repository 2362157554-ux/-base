# 第三方许可证与致谢

本项目 **-base**（"一句话剪辑"）在架构与算法思路上参考了以下开源项目，但本仓库内
**不包含这些项目的源代码**——所有代码均为本项目作者在阅读上游文档与公开 schema
后重新实现。下列项目使用 MIT License 发布，在此致谢：

| 项目 | 仓库 | 用途 | 许可证 |
|---|---|---|---|
| pyJianYingDraft | https://github.com/GuanYixuan/pyJianYingDraft | 剪映草稿 schema 设计参考（`draft_content.json`、时间区间、轨道/片段结构） | MIT |
| Remotion | https://github.com/remotion-dev/remotion | React 端帧渲染思路参考（`<Composition>` 数据驱动、Player 预览、`renderMedia` 思路） | MIT |

完整的上游 LICENSE 文本保留在项目审计目录 `reference/_licenses/` 下，仅供溯源
与对照，不随产品分发。

## 重写说明

- 我们没有 vendor 任何 `.py` 或 `.ts` 文件。
- 我们没有 fork 任何上游仓库。
- 我们以"读过之后自己写"的方式构建本仓库，因此代码风格、命名、模块切分与
  上游均不同。
- 上游任何 BUG 或限制我们均不继承；如果你需要原汁原味的功能，请直接使用上游。

## 上游 LICENSE 摘录（MIT）

> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software ...

完整文本见 https://opensource.org/licenses/MIT 。
