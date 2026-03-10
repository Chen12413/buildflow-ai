# BuildFlow AI API Spec v0.1

## 1. 文档信息

- 产品名称：BuildFlow AI
- 文档版本：v0.1
- 文档类型：API 规格说明
- 对应架构文档：`docs/architecture-v0.1.md`
- 对应 PRD：`docs/prd-v0.1.md`

## 2. 设计原则

- 基础路径：`/api/v1`
- 协议：`REST + JSON`
- ID 类型：`UUID`
- 时间格式：`ISO 8601`
- 所有写操作默认返回最新资源或运行状态
- 所有错误返回统一结构

## 3. 通用响应结构

### 3.1 成功响应

```json
{
  "data": {},
  "meta": null
}
```

### 3.2 失败响应

```json
{
  "code": "validation_error",
  "message": "Request validation failed",
  "details": {}
}
```

## 4. 枚举定义

### 4.1 Platform

- `web`
- `mobile`
- `both`

### 4.2 RunType

- `clarification_generation`
- `prd_generation`

### 4.3 RunStatus

- `pending`
- `running`
- `completed`
- `failed`

### 4.4 ArtifactType

- `prd`

## 5. 数据契约

### 5.1 Project

```json
{
  "id": "uuid",
  "name": "BuildFlow AI",
  "idea": "一个帮助用户快速生成产品PRD的AI工具",
  "target_user": "独立开发者与产品经理",
  "platform": "web",
  "constraints": "一天内完成MVP",
  "created_at": "2026-03-10T10:00:00Z",
  "updated_at": "2026-03-10T10:00:00Z"
}
```

### 5.2 ClarificationQuestion

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "question": "这个产品要优先解决用户的哪个核心痛点？",
  "order_index": 1,
  "created_at": "2026-03-10T10:00:00Z"
}
```

### 5.3 ClarificationAnswer

```json
{
  "question_id": "uuid",
  "answer": "希望帮助用户快速从想法进入结构化需求定义"
}
```

### 5.4 Run

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "type": "prd_generation",
  "status": "running",
  "error_message": null,
  "created_at": "2026-03-10T10:00:00Z",
  "completed_at": null
}
```

### 5.5 PRD Artifact

```json
{
  "id": "uuid",
  "project_id": "uuid",
  "run_id": "uuid",
  "type": "prd",
  "version": 1,
  "content_json": {
    "product_summary": "...",
    "problem_statement": "...",
    "target_users": ["..."],
    "core_scenarios": ["..."],
    "mvp_goal": "...",
    "in_scope": ["..."],
    "out_of_scope": ["..."],
    "user_stories": ["..."],
    "success_metrics": ["..."],
    "risks": ["..."]
  },
  "content_markdown": "# PRD\n...",
  "created_at": "2026-03-10T10:00:00Z"
}
```

## 6. 接口清单

- `POST /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/clarifications/generate`
- `PUT /api/v1/projects/{project_id}/clarifications/answers`
- `POST /api/v1/projects/{project_id}/prd/generate`
- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/projects/{project_id}/artifacts/prd/latest`
- `GET /api/v1/projects/{project_id}/export/markdown`

## 7. 接口详情

### 7.1 创建项目

**请求**

- Method：`POST`
- Path：`/api/v1/projects`

**Request Body**

```json
{
  "name": "BuildFlow AI",
  "idea": "一个帮助用户把产品想法变成PRD的AI工具",
  "target_user": "独立开发者、产品经理",
  "platform": "web",
  "constraints": "一天内完成MVP"
}
```

**字段约束**

- `name`：必填，1-100 字符
- `idea`：必填，1-500 字符
- `target_user`：必填，1-300 字符
- `platform`：必填，枚举值
- `constraints`：可选，0-1000 字符

**Success 201**

```json
{
  "data": {
    "id": "uuid",
    "name": "BuildFlow AI",
    "idea": "一个帮助用户把产品想法变成PRD的AI工具",
    "target_user": "独立开发者、产品经理",
    "platform": "web",
    "constraints": "一天内完成MVP",
    "created_at": "2026-03-10T10:00:00Z",
    "updated_at": "2026-03-10T10:00:00Z"
  },
  "meta": null
}
```

### 7.2 获取项目详情

**请求**

- Method：`GET`
- Path：`/api/v1/projects/{project_id}`

**Success 200**

```json
{
  "data": {
    "id": "uuid",
    "name": "BuildFlow AI",
    "idea": "一个帮助用户把产品想法变成PRD的AI工具",
    "target_user": "独立开发者、产品经理",
    "platform": "web",
    "constraints": "一天内完成MVP",
    "created_at": "2026-03-10T10:00:00Z",
    "updated_at": "2026-03-10T10:00:00Z"
  },
  "meta": null
}
```

### 7.3 生成澄清问题

**请求**

- Method：`POST`
- Path：`/api/v1/projects/{project_id}/clarifications/generate`

**Request Body**

```json
{}
```

**Success 200**

```json
{
  "data": {
    "run": {
      "id": "uuid",
      "project_id": "uuid",
      "type": "clarification_generation",
      "status": "completed",
      "error_message": null,
      "created_at": "2026-03-10T10:00:00Z",
      "completed_at": "2026-03-10T10:00:05Z"
    },
    "questions": [
      {
        "id": "uuid",
        "project_id": "uuid",
        "question": "这个产品最优先解决什么问题？",
        "order_index": 1,
        "created_at": "2026-03-10T10:00:05Z"
      }
    ]
  },
  "meta": null
}
```

**说明**

- v0.1 默认同步返回结果，若后续改为异步，只保留 `run_id` 并通过 `GET /runs/{run_id}` 查询

### 7.4 提交澄清答案

**请求**

- Method：`PUT`
- Path：`/api/v1/projects/{project_id}/clarifications/answers`

**Request Body**

```json
{
  "answers": [
    {
      "question_id": "uuid",
      "answer": "帮助独立开发者快速明确项目需求"
    },
    {
      "question_id": "uuid",
      "answer": "首版只做PRD生成，不做代码生成"
    }
  ]
}
```

**Success 200**

```json
{
  "data": {
    "project_id": "uuid",
    "saved_count": 2
  },
  "meta": null
}
```

### 7.5 生成 PRD

**请求**

- Method：`POST`
- Path：`/api/v1/projects/{project_id}/prd/generate`

**Request Body**

```json
{}
```

**Success 202**

```json
{
  "data": {
    "run": {
      "id": "uuid",
      "project_id": "uuid",
      "type": "prd_generation",
      "status": "running",
      "error_message": null,
      "created_at": "2026-03-10T10:10:00Z",
      "completed_at": null
    }
  },
  "meta": null
}
```

**说明**

- 生成 PRD 采用后台任务，前端轮询 `GET /api/v1/runs/{run_id}`

### 7.6 获取运行状态

**请求**

- Method：`GET`
- Path：`/api/v1/runs/{run_id}`

**Success 200（运行中）**

```json
{
  "data": {
    "id": "uuid",
    "project_id": "uuid",
    "type": "prd_generation",
    "status": "running",
    "error_message": null,
    "created_at": "2026-03-10T10:10:00Z",
    "completed_at": null
  },
  "meta": null
}
```

**Success 200（完成）**

```json
{
  "data": {
    "id": "uuid",
    "project_id": "uuid",
    "type": "prd_generation",
    "status": "completed",
    "error_message": null,
    "created_at": "2026-03-10T10:10:00Z",
    "completed_at": "2026-03-10T10:10:08Z"
  },
  "meta": {
    "artifact_ready": true
  }
}
```

### 7.7 获取最新 PRD

**请求**

- Method：`GET`
- Path：`/api/v1/projects/{project_id}/artifacts/prd/latest`

**Success 200**

```json
{
  "data": {
    "id": "uuid",
    "project_id": "uuid",
    "run_id": "uuid",
    "type": "prd",
    "version": 1,
    "content_json": {
      "product_summary": "BuildFlow AI 帮助用户把想法转成结构化PRD",
      "problem_statement": "用户缺少稳定的需求整理方式",
      "target_users": ["独立开发者", "产品经理"],
      "core_scenarios": ["项目启动", "面试作品展示"],
      "mvp_goal": "10分钟内得到一份可导出的PRD",
      "in_scope": ["项目创建", "澄清问题", "PRD生成", "导出Markdown"],
      "out_of_scope": ["架构生成", "任务拆解", "测试生成"],
      "user_stories": ["作为独立开发者，我希望快速获得PRD"],
      "success_metrics": ["PRD生成成功率 > 90%"],
      "risks": ["输入过少导致结果空泛"]
    },
    "content_markdown": "# BuildFlow AI PRD\n...",
    "created_at": "2026-03-10T10:10:08Z"
  },
  "meta": null
}
```

### 7.8 导出 Markdown

**请求**

- Method：`GET`
- Path：`/api/v1/projects/{project_id}/export/markdown`

**Success 200**

- `Content-Type: text/markdown; charset=utf-8`
- `Content-Disposition: attachment; filename="buildflow-ai-prd-v1.md"`

**Response Body**

```markdown
# 产品概述
...
```

## 8. 典型错误码

- `validation_error`
- `project_not_found`
- `clarification_questions_not_found`
- `clarification_answers_missing`
- `run_not_found`
- `artifact_not_found`
- `workflow_failed`
- `llm_provider_error`

## 9. 状态流转规则

### 9.1 Clarification Generation

- `pending -> running -> completed`
- `pending -> running -> failed`

### 9.2 PRD Generation

- `pending -> running -> completed`
- `pending -> running -> failed`

## 10. 第 3 步开发建议

后续实现顺序建议严格按以下顺序：

1. `Project` schema + model + create/get API
2. `Clarification` schema + generate/save API
3. `Run` schema + status API
4. `PRD` schema + artifact 存储
5. `Export` API
6. 前端页面联调
7. 测试补齐
