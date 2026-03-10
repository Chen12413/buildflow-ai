# BuildFlow AI Architecture v0.1

## 1. 文档信息

- 产品名称：BuildFlow AI
- 文档版本：v0.1
- 文档类型：系统架构设计文档
- 对应 PRD：`docs/prd-v0.1.md`
- 目标阶段：支撑 v0.1 的实现与联调

## 2. 架构目标

本架构只服务于 v0.1 的唯一主链路：

**Idea Input → Clarification → PRD Generation → Review & Export**

架构设计目标如下：

- 以最小复杂度支撑一条完整业务闭环
- 保证输出结构化、可测试、可追踪
- 保证前后端边界清晰，避免原型式耦合
- 为后续扩展 Architecture、Tasks、Tests 等 artifact 预留稳定接口
- 保持一天内可完成 MVP 的工程节奏

## 3. 设计原则

### 3.1 KISS

- 不引入消息队列、微服务、事件总线
- 不做多 Agent 自由协商
- 不做复杂状态机
- 优先采用单体分层架构

### 3.2 YAGNI

- 当前只支持 `prd` 一种 artifact
- 当前只支持单用户、自主使用场景
- 当前只实现 Markdown 导出，不做多格式导出

### 3.3 DRY

- 所有 LLM 调用走统一 Provider 接口
- 所有 Prompt 走独立模板层
- 所有 API 返回走统一响应结构
- 所有持久化访问走 Repository 层

### 3.4 SOLID

- Router 只处理 HTTP 协议
- Service 只处理业务编排
- Repository 只处理数据访问
- Prompt 模板与 Workflow 分离
- LLM Provider 依赖抽象接口而不是具体 SDK

## 4. 范围与边界

### 4.1 In Scope

- 项目创建
- 澄清问题生成
- 澄清答案保存
- PRD 生成
- PRD 在线查看
- Markdown 导出
- 运行状态查询

### 4.2 Out of Scope

- 用户登录与权限系统
- 团队协作
- 多项目空间管理
- RAG / 向量检索
- API 设计生成
- 架构设计生成
- 任务拆解生成
- 测试用例生成
- 任务队列与分布式执行

## 5. 技术选型

### 5.1 前端

- 框架：`Next.js`（App Router）
- 语言：`TypeScript`
- UI：`Tailwind CSS` + `shadcn/ui`
- 表单：`react-hook-form`
- 校验：`zod`
- 测试：`Vitest` + `Playwright`

### 5.2 后端

- 框架：`FastAPI`
- 数据校验：`Pydantic v2`
- ORM：`SQLAlchemy 2.0`
- 数据迁移：`Alembic`
- 测试：`pytest` + `httpx` / `TestClient`

### 5.3 数据存储

- 开发环境：`SQLite`
- 生产升级路径：`PostgreSQL`

### 5.4 异步执行

- v0.1：`FastAPI BackgroundTasks`
- 后续升级：任务量增加后迁移到独立队列

### 5.5 导出能力

- 输出格式：`Markdown`
- 渲染方式：后端保存 `content_json` 与 `content_markdown`

## 6. 关键技术决策与理由

### 6.1 为什么前端使用 Next.js App Router

- 官方将 App Router 作为现代推荐的路由与渲染组织方式，适合基于页面和数据边界组织目录
- 适合把只读展示页尽可能做成 Server Component，把交互表单隔离在 Client Component
- 便于后续接入部署平台与测试链路

### 6.2 为什么后端使用 FastAPI

- 天然支持基于类型的请求/响应 schema 定义
- 自动产出 OpenAPI，方便前后端联调
- 对于 MVP，能以较低成本建立清晰的分层 API 服务

### 6.3 为什么 v0.1 使用 REST + JSON

- 当前只有单前端、单后端、单业务闭环
- REST 最适合快速联调、调试、测试和文档化
- `gRPC`、事件驱动、GraphQL 都会提高实现复杂度，不符合当前目标

### 6.4 为什么 v0.1 使用 BackgroundTasks 而不是消息队列

- 官方将 BackgroundTasks 作为适合小型后台作业的方案
- PRD 生成属于可控时长任务，MVP 可先在同进程内完成
- 后续如果 LLM 调用耗时或并发增加，再迁移队列系统

### 6.5 为什么 ORM 选 SQLAlchemy 2.0 + Alembic

- SQLAlchemy 2.0 风格更适合明确模型边界与类型约束
- Alembic 可为未来切换 PostgreSQL 保留迁移路径
- 相较直接裸 SQL，更利于维护和演进

## 7. 系统上下文

### 7.1 参与方

- 用户：通过 Web 页面创建项目与查看 PRD
- 前端 Web：负责交互、页面渲染、轮询状态
- 后端 API：负责业务编排、LLM 调用、持久化
- LLM Provider：负责生成澄清问题与 PRD
- 数据库：保存项目、问题、回答、运行记录、产物

### 7.2 系统边界

- 浏览器只与 `Next.js` 页面交互
- `Next.js` 前端通过 HTTP 调用 `FastAPI`
- `FastAPI` 是唯一业务入口
- 所有模型生成都由后端统一封装

## 8. 总体架构

```text
[Browser]
   |
   v
[Next.js Web]
   |
   | HTTP/JSON
   v
[FastAPI API]
   |
   +--> [Workflow Service]
   |        |
   |        +--> [Prompt Templates]
   |        +--> [LLM Provider]
   |
   +--> [Repositories]
   |
   v
[SQLite / PostgreSQL]
```

## 9. 前端架构设计

### 9.1 目录建议

```text
web/
  app/
    page.tsx
    projects/
      new/page.tsx
      [projectId]/clarify/page.tsx
      [projectId]/prd/page.tsx
  components/
  features/
    projects/
    clarifications/
    prd/
  lib/
    api-client.ts
    schemas.ts
  tests/
```

### 9.2 页面职责

- `app/page.tsx`：营销首页与产品入口
- `app/projects/new/page.tsx`：项目创建表单
- `app/projects/[projectId]/clarify/page.tsx`：显示澄清问题、收集回答
- `app/projects/[projectId]/prd/page.tsx`：展示 PRD、导出 Markdown

### 9.3 前端数据流

- 表单提交后调用后端 REST API
- 对耗时任务采用轮询 `run status`
- 对结构化结果只做展示，不在前端拼接业务逻辑
- 所有接口类型与后端 schema 对齐

### 9.4 组件边界

- 页面容器组件负责数据获取和路由跳转
- 表单组件负责输入与校验
- 结果展示组件只负责渲染 PRD 结构
- 导出组件只负责下载或复制动作

### 9.5 状态管理策略

- v0.1 不引入全局状态库
- 页面级状态使用 React 内置状态管理
- 可选使用 `SWR` 或 `TanStack Query` 做轮询与缓存；若时间紧，先用原生 `fetch`

## 10. 后端架构设计

### 10.1 目录建议

```text
api/
  app/
    main.py
    core/
      config.py
      logging.py
    db/
      session.py
      base.py
    models/
      project.py
      clarification.py
      run.py
      artifact.py
    schemas/
      common.py
      project.py
      clarification.py
      prd.py
      run.py
      artifact.py
    repositories/
      project_repository.py
      clarification_repository.py
      run_repository.py
      artifact_repository.py
    routers/
      projects.py
      clarifications.py
      prd.py
      runs.py
      exports.py
    services/
      project_service.py
      clarification_service.py
      prd_service.py
      export_service.py
    workflows/
      clarification_workflow.py
      prd_workflow.py
    prompts/
      clarification_prompt.py
      prd_prompt.py
    llm/
      base.py
      provider.py
```

### 10.2 分层职责

- `routers`：接收请求、做基础校验、返回响应
- `services`：组织用例，处理事务边界
- `workflows`：处理 LLM 生成步骤
- `prompts`：管理模板与输出约束
- `repositories`：访问数据库
- `schemas`：统一输入输出契约
- `models`：ORM 数据模型
- `llm`：供应商抽象与模型调用封装

### 10.3 为什么不用“一个大 service”

- 会快速演化为不可维护的巨型文件
- Prompt、业务流程、数据访问会耦合在一起
- 难以测试，也不利于后续扩展新的 artifact 类型

## 11. Workflow 设计

### 11.1 Clarification Workflow

输入：

- 项目基础信息
- 可选约束

输出：

- 3 到 5 个澄清问题

步骤：

1. 读取项目基础信息
2. 拼接澄清 Prompt
3. 调用 LLM
4. 校验输出 schema
5. 保存问题列表
6. 更新 run 状态

### 11.2 PRD Workflow

输入：

- 项目基础信息
- 澄清问题与答案

输出：

- `content_json`
- `content_markdown`

步骤：

1. 聚合项目输入与澄清答案
2. 拼接 PRD Prompt
3. 调用 LLM
4. 校验 PRD schema
5. 渲染 Markdown
6. 保存 artifact
7. 更新 run 状态

### 11.3 重要约束

- Workflow 只允许生成结构化 JSON
- Markdown 由后端根据结构化 JSON 渲染
- 不允许前端直接消费原始大模型自由文本

## 12. 数据模型设计

### 12.1 Project

- `id`: UUID
- `name`: 项目名称
- `idea`: 一句话想法
- `target_user`: 目标用户描述
- `platform`: `web | mobile | both`
- `constraints`: 可选约束文本
- `created_at`
- `updated_at`

### 12.2 ClarificationQuestion

- `id`: UUID
- `project_id`: 关联项目
- `question`: 问题内容
- `order_index`: 排序
- `created_at`

### 12.3 ClarificationAnswer

- `id`: UUID
- `project_id`: 关联项目
- `question_id`: 关联问题
- `answer`: 回答内容
- `created_at`

### 12.4 Run

- `id`: UUID
- `project_id`: 关联项目
- `type`: `clarification_generation | prd_generation`
- `status`: `pending | running | completed | failed`
- `error_message`: 失败原因
- `created_at`
- `completed_at`

### 12.5 Artifact

- `id`: UUID
- `project_id`: 关联项目
- `run_id`: 来源运行记录
- `type`: `prd`
- `content_json`: 结构化 JSON
- `content_markdown`: Markdown 文本
- `version`: 默认从 `1` 开始
- `created_at`

### 12.6 关系说明

- 一个 `Project` 可有多条 `ClarificationQuestion`
- 一个 `Project` 可有多条 `ClarificationAnswer`
- 一个 `Project` 可有多次 `Run`
- 一个 `Project` 可有多版 `Artifact`
- 一个 `Artifact` 对应一次 `PRD Run`

## 13. 前后端链路设计

### 13.1 创建项目链路

1. 用户在前端填写基础信息
2. 前端调用 `POST /api/v1/projects`
3. 后端创建 `Project`
4. 前端跳转到澄清页

### 13.2 生成澄清问题链路

1. 前端调用 `POST /api/v1/projects/{project_id}/clarifications/generate`
2. 后端创建 `Run`
3. 后端执行 Clarification Workflow
4. 保存问题列表
5. 返回 `run_id` 与问题结果

### 13.3 提交回答链路

1. 用户填写答案
2. 前端调用 `PUT /api/v1/projects/{project_id}/clarifications/answers`
3. 后端保存回答
4. 前端允许用户触发 PRD 生成

### 13.4 生成 PRD 链路

1. 前端调用 `POST /api/v1/projects/{project_id}/prd/generate`
2. 后端创建 `Run`
3. 后台执行 PRD Workflow
4. 生成结构化 PRD 与 Markdown
5. 保存 `Artifact`
6. 前端轮询 `GET /api/v1/runs/{run_id}`
7. 完成后跳转 PRD 结果页

### 13.5 导出链路

1. 前端请求 `GET /api/v1/projects/{project_id}/export/markdown`
2. 后端读取最新 PRD artifact
3. 返回 Markdown 文本或文件下载响应

## 14. API 协议设计

### 14.1 协议选择

- 协议：`HTTP/1.1` 或 `HTTP/2`
- 风格：`REST`
- 编码：`JSON`
- 时间格式：`ISO 8601`
- ID 类型：`UUID`

### 14.2 为什么当前不使用 gRPC

- 浏览器端直接接入成本更高
- 调试门槛更高
- 当前业务模型简单，不需要强制引入 RPC 框架
- FastAPI 自动 OpenAPI 已足够支撑当前联调效率

### 14.3 API 版本策略

- 统一前缀：`/api/v1`
- 非兼容变更进入 `v2`
- 兼容字段新增在 `v1` 内迭代

### 14.4 错误响应统一结构

```json
{
  "code": "project_not_found",
  "message": "Project not found",
  "details": null
}
```

## 15. LLM 集成设计

### 15.1 抽象层

定义统一接口：

- `generate_clarification_questions(input) -> ClarificationQuestionList`
- `generate_prd(input) -> PRDDocument`

### 15.2 Prompt 设计原则

- Prompt 与业务逻辑分离
- Prompt 输出只允许 JSON schema
- Prompt 模板版本化管理
- 禁止在 Router 中拼 Prompt

### 15.3 输出控制

- 使用 Pydantic schema 严格校验
- 校验失败视为 workflow 失败
- 失败信息写入 `Run.error_message`

## 16. 可观测性与日志

### 16.1 日志要求

- 每个请求生成 `request_id`
- 每个 workflow 记录 `run_id`
- 记录开始时间、结束时间、状态、错误信息

### 16.2 最小监控指标

- 项目创建成功数
- 澄清问题生成成功率
- PRD 生成成功率
- PRD 平均生成耗时
- 失败原因分布

## 17. 安全与配置

### 17.1 配置项

- `API_BASE_URL`
- `DATABASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`
- `CORS_ALLOW_ORIGINS`

### 17.2 安全基线

- API key 只保存在后端
- 前端不直连模型供应商
- CORS 使用白名单
- 对用户输入做长度限制
- 对导出接口做项目存在性校验

### 17.3 当前不做的安全能力

- 用户鉴权
- RBAC
- 细粒度审计
- 限流平台

## 18. 测试策略

### 18.1 后端测试

- `schema` 单元测试
- `repository` 集成测试
- `workflow` 测试
- API 路由测试
- 导出逻辑测试

### 18.2 前端测试

- 新建项目表单提交流程
- 澄清问答提交流程
- PRD 结果渲染
- 导出按钮行为

### 18.3 端到端测试主链路

- 创建项目
- 生成问题
- 回答问题
- 生成 PRD
- 查看结果
- 导出 Markdown

## 19. 部署建议

### 19.1 本地开发

- 前端：`Next.js dev server`
- 后端：`uvicorn`
- 数据库：`SQLite`

### 19.2 演示部署

- 前端：`Vercel`
- 后端：`Render` / `Railway` / `Fly.io`
- 数据库：演示环境建议切换到 `PostgreSQL`

### 19.3 为什么演示环境不建议继续使用 SQLite

- 文件数据库不适合多实例部署
- 平台文件系统持久性通常不稳定
- 后续升级 PostgreSQL 更利于公开演示与恢复

## 20. 风险与缓解

### 20.1 LLM 输出不稳定

- 缓解：强制 schema 输出 + 校验失败重试一次

### 20.2 用户输入过少导致 PRD 空泛

- 缓解：澄清问题固定覆盖痛点、场景、范围、目标

### 20.3 后台任务阻塞

- 缓解：v0.1 限制并发与输入长度；v0.2 再升级队列

### 20.4 前后端字段漂移

- 缓解：共享 schema 定义与 API spec 文档

## 21. 第 3 步实现输入

第 3 步开发必须严格围绕以下范围进行：

- 只搭建 4 个页面
- 只实现 5 个核心实体
- 只实现 7 组 API
- 只实现 2 个 workflow
- 只输出 1 种 artifact：`prd`

任何新增需求都应进入后续版本，而不是插入 v0.1。

## 22. 官方依据

- Next.js App Router：`https://nextjs.org/docs/app`
- Next.js Testing：`https://nextjs.org/docs/app/guides/testing`
- FastAPI Background Tasks：`https://fastapi.tiangolo.com/tutorial/background-tasks/`
- FastAPI Testing：`https://fastapi.tiangolo.com/tutorial/testing/`
- SQLAlchemy 2.0：`https://docs.sqlalchemy.org/en/20/`
- Alembic Autogenerate：`https://alembic.sqlalchemy.org/en/latest/autogenerate.html`
