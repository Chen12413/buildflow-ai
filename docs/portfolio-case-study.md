# BuildFlow AI 项目案例拆解

## 一句话定位

BuildFlow AI 是一个基于 `Next.js + FastAPI` 的 AI Agent 工作流项目，目标是把“模糊产品想法”稳定推进成“可交付、可演示、可继续开发”的结构化产物。

## 这个项目解决什么问题

很多 AI 原型项目只能快速做出一个页面或一个功能点，但存在三个典型问题：

- 代码结构差，后续很难维护和继续迭代
- 业务链路断裂，用户只能看到单点生成结果
- 缺少测试、部署、文档和展示素材，难以写进简历和长期运营

BuildFlow AI 的核心思路，就是把这些短板补齐，做成一个真正可持续迭代的个人项目。

## 目标用户

- AI 产品经理
- 独立开发者 / Indie Hacker
- 早期创业团队
- 需要快速验证需求并沉淀文档的 PM / Builder

## 主链路设计

1. **创建项目**：输入产品想法、目标用户、平台和限制条件
2. **澄清问题**：由 Agent 自动提出补充问题，减少模糊输入
3. **生成 PRD**：将澄清后的内容整理成结构化产品文档
4. **生成开发规划**：输出 MVP 范围、模块划分、阶段目标和风险
5. **任务拆解**：按模块拆成可执行任务，便于继续开发
6. **生成 Demo**：用多 Agent 产出一个可直接展示的简单产品 Demo

## 多 Agent 设计

- **Clarification Agent**：负责识别信息缺口并生成澄清问题
- **PRD Agent**：负责把上下文压缩成结构化 PRD 文档
- **Planning Agent**：负责把 PRD 转成开发规划、里程碑和实施建议
- **Task Breakdown Agent**：负责做模块级任务拆分和交付建议
- **Demo Agent**：负责生成可展示的 Demo 页面结构与交互说明

这种设计让每个 Agent 只负责一个明确职责，既便于写 Prompt，也便于后续单独调优。

## 技术方案

- **前端**：`Next.js 15`、`React 19`、`TypeScript`、`Tailwind CSS`
- **后端**：`FastAPI`、`SQLAlchemy`、`Pydantic Settings`、`SQLite`
- **模型层**：支持 `mock` 与 `阿里云百炼`，并实现 `responses 优先 + chat-completions 兼容后备`
- **工程化**：`pytest`、`Playwright`、`GitHub Actions`、`Docker`、`Render`

## 工程亮点

- **可维护性优先**：按服务、路由、Schema、Prompt、Workflow 分层，而不是把逻辑堆在一个函数里
- **测试闭环**：后端单测、前端构建检查、Playwright E2E 全链路回归都可运行
- **稳定副本方案**：针对 OneDrive 目录下 Next.js 容易卡住的问题，增加稳定副本工作流脚本
- **自动截图素材**：可一键生成首页、PRD、规划、任务拆解、Demo 与 Agent 面板截图
- **可发布化**：具备 README、LICENSE、CI、部署文档、线上 Demo 和展示素材

## 可验证成果

- `powershell -ExecutionPolicy Bypass -File .\scripts\test.ps1`：通过后端测试与前端构建检查
- `powershell -ExecutionPolicy Bypass -File .\scripts\e2e.ps1`：完整跑通从创建项目到 Demo 的 E2E 主链路
- `powershell -ExecutionPolicy Bypass -File .\scripts\showcase.ps1`：自动产出 10 张展示截图
- `powershell -ExecutionPolicy Bypass -File .\scripts\web-preview.ps1`：在稳定副本中完成生产构建并启动预览

## 为什么适合写进简历

- 它展示的不是“会调 API”，而是“会设计一条 AI 产品业务链路”
- 它展示的不是“能写 Demo”，而是“能把 Demo 做成可维护、可测试、可部署的项目”
- 它同时覆盖了产品视角、Prompt 设计、多 Agent 协作、工程化和上线展示

## 推荐面试讲法

可以把这个项目讲成三层：

1. **业务层**：为什么要从想法一路推进到 PRD、规划、任务拆解和 Demo
2. **AI 层**：为什么用多 Agent / 多 Prompt 分工，而不是一个超长 Prompt
3. **工程层**：如何解决测试、部署、OneDrive 稳定性和作品集展示问题

## 相关资料

- README：`README.md`
- 简历文案：`docs/profile-copy.md`
- 展示素材说明：`docs/showcase-kit.md`
- 自动截图产物：`docs/assets/screenshots`
