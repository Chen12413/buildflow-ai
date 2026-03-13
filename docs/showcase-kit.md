# BuildFlow AI 展示素材包

这份文件用于整理 GitHub 仓库展示、个人主页卡片、社媒封面图和截图素材的推荐用法。

## 推荐展示结构

### 1. GitHub 仓库首页

- 仓库名：`buildflow-ai`
- 简介：`AI workflow platform that turns product ideas into clarification, PRD, planning, task breakdown, and multi-agent demo outputs.`
- 置顶图片：`docs/assets/social-preview.svg`
- 推荐截图顺序：
  - `docs/assets/screenshots/home.png`
  - `docs/assets/screenshots/new-project.png`
  - `docs/assets/screenshots/clarification.png`
  - `docs/assets/screenshots/prd.png`
  - `docs/assets/screenshots/planning.png`
  - `docs/assets/screenshots/task-breakdown.png`
  - `docs/assets/screenshots/demo-overview.png`
  - `docs/assets/screenshots/demo-studio.png`
  - `docs/assets/screenshots/agent-panel.png`

### 2. 个人主页 / 作品集卡片

- 标题：`BuildFlow AI`
- 副标题：`从产品想法到产品快速实现的 AI 工作流平台`
- 一句话卖点：`不是只做一个原型页面，而是把需求澄清、文档生成、任务拆解和演示输出串成一条可维护主链路。`
- 补充卖点：`页面内置长任务状态面板、动态进度条和多 Agent 展示层，更适合公开演示“从想法到产品”的完整过程。`

## 项目亮点文案

### 面向招聘方的版本

- `围绕真实产品交付流程，而不是单点大模型调用，设计了从 Idea 到产品 Demo 的完整 AI 业务链路。`
- `兼顾产品经理视角与工程视角：既强调 PRD、规划和演示价值，也补齐了 Provider 抽象、测试、部署、截图自动化和长任务体验。`
- `适合作为“长期性个人项目”展示，能够同时覆盖 AI 产品思维、系统设计和工程可维护性。`

### 面向作品集访客的版本

- `BuildFlow AI 帮你把模糊产品想法转成结构化产物，并最终输出一个可以直接展示的目标产品 Demo。`
- `项目重点不在“让模型生成一句答案”，而在“让用户沿着主链路持续推进产品交付”。`
- `就算任务耗时较长，页面也会持续给出进度、状态和后续动作提示，演示体验更完整。`

## 自动截图

### 一键生成展示素材

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\showcase.ps1
```

### OneDrive 环境推荐

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\showcase.ps1 -UseStableWebCopy
```

## 稳定构建 / 生产预览

### 一键稳定构建并启动预览

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\web-preview.ps1
```

### 仅构建不启动

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\web-preview.ps1 -BuildOnly
```

## 推荐截图说明

- `home.png`：项目首页，用于展示价值主张与完整主链路
- `new-project.png`：项目创建输入页，用于说明业务入口
- `clarification.png`：澄清页面，用于展示结构化问答能力
- `prd.png`：PRD 结果页，用于展示文档生成能力
- `planning.png`：开发规划页，用于展示工程化落地能力
- `task-breakdown.png`：模块任务拆解页，用于展示多 Agent 扩展与测试前置
- `demo-overview.png`：Demo 总览页，用于展示面试友好的可视化结果
- `demo-studio.png`：目标产品 Demo 细节图，当前推荐使用 `AI 旅游规划` 示例，展示用户真正会看到的产品界面
- `agent-panel.png`：多 Agent 运行面板，用于展示 Prompt 可视化与职责分工
- `任务进行中的状态页`：用于展示长任务进度反馈、状态引导和页面观感优化

## 推荐演示顺序

1. 首页：解释这不是单点功能，而是完整业务链路
2. 新建项目：说明输入约束与目标用户
3. 澄清：展示模型如何先补信息再生成文档
4. PRD / Planning / Task Breakdown：说明结构化输出如何服务开发
5. 目标产品 Demo：展示多 Agent 最终如何把文档变成一个可演示、可理解、可拿去讲解的用户产品结果
