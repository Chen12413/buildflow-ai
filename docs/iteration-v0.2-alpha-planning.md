# BuildFlow AI Iteration v0.2-alpha

## 目标

在不破坏 `v0.1` 主链路的前提下，完成原始开发排期中的第 4 步：接入第三个 Agent —— `Planning Agent`。

## 本次新增能力

- 新增 `planning_generation` 运行类型
- 新增 `planning` artifact 类型
- 新增 Planning Workflow、Service、Router
- 新增 Planning 查看页与 Markdown 导出能力
- 从 `PRD` 结果页可直接触发 Planning 生成

## 新增业务链路

`PRD -> Planning Generation -> Review & Export`

## 产物结构

Planning 产物包含以下内容：

- 目标
- 交付策略
- 里程碑
- 任务与验收标准
- 依赖项
- 测试重点
- 发布说明

## 兼容性说明

- `v0.1` 文档仍然成立，因为它描述的是首个最小主链路
- Planning 能力作为后续迭代扩展，不改变原始 `Idea -> Clarification -> PRD` 路径
