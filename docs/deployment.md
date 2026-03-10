# BuildFlow AI Deployment Guide

This project supports two deployment paths:

- **Recommended: Render Blueprint** for a public online demo
- **Local: Docker Compose demo stack** for fast end-to-end verification

## 1. Recommended: Render Blueprint

### 1.1 Topology

The repository includes a ready-to-use `render.yaml` at the repo root. It creates two services by default:

- `chen12413-buildflow-api`
  - Type: public `Web Service`
  - Purpose: FastAPI backend
  - Plan: `free`
- `chen12413-buildflow-web`
  - Type: public `Web Service`
  - Purpose: Next.js frontend
  - Plan: `free`

The frontend still uses same-origin `/api/*`, and the Next.js route handler forwards requests to `API_PROXY_TARGET`. On Render, that value is injected automatically from the API service through `fromService.envVarKey: RENDER_EXTERNAL_URL`.

### 1.2 Why no credit card is required now

A previous setup used `Private Service + starter`, which triggered payment requirements. The current Blueprint uses two public free web services instead, which is more suitable for a personal demo project without an overseas credit card.

The tradeoff is that the backend now has a public `onrender.com` URL. In practice, users still only need to open the frontend site because browser traffic continues to go through the frontend and its server-side proxy.

### 1.3 One-click deploy entry

- Render deploy button: `https://render.com/deploy?repo=https://github.com/Chen12413/buildflow-ai`
- Official docs:
  - Blueprint Spec: `https://render.com/docs/blueprint-spec`
  - Deploy to Render Button: `https://render.com/docs/deploy-to-render-button`
  - Web Services: `https://render.com/docs/web-services`
  - Free Instances: `https://render.com/docs/free`

### 1.4 Default runtime behavior

The Blueprint uses the following defaults.

#### API default environment

```env
DATABASE_URL=sqlite+pysqlite:///./buildflow.db
LLM_PROVIDER=mock
LLM_MODEL=mock-buildflow-v1
LLM_API_MODE=auto
```

#### Web default environment

```env
NEXT_PUBLIC_API_BASE_URL=
API_PROXY_TARGET=<auto-injected from chen12413-buildflow-api RENDER_EXTERNAL_URL>
```

With this setup, the first deployment requires no API key and no credit card, and the full main flow can be demonstrated immediately.

### 1.5 Switching to Aliyun Bailian

After deployment, open `chen12413-buildflow-api` in Render and add these environment variables:

```env
LLM_PROVIDER=aliyun_bailian
LLM_MODEL=qwen3.5-plus
LLM_API_MODE=auto
DASHSCOPE_API_KEY=<your-bailian-api-key>
```

These endpoint variables usually do not need to change:

```env
DASHSCOPE_CHAT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_RESPONSES_BASE_URL=https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1
```

### 1.6 Important limitations

The current demo uses SQLite inside the container, which is fine for a public demo but not ideal for production:

- Data may be lost after restart or redeploy
- SQLite is not suitable for multi-instance scale-out
- Long-term persistence should move to Postgres or another durable storage option

### 1.7 Suggested rollout steps

1. Open `https://render.com/deploy?repo=https://github.com/Chen12413/buildflow-ai`
2. Sign in to Render and import the repo Blueprint
3. Keep the default names or rename the services if needed
4. Deploy with the default `mock` provider first
5. After the main flow works, add Bailian API variables to `chen12413-buildflow-api`
6. Fill your GitHub repository About website field with the live demo URL

## 2. Local Docker Compose Demo

The repo already includes:

- `api/Dockerfile`
- `web/Dockerfile`
- `docker-compose.demo.yml`

Start the stack with:

```powershell
docker compose -f .\docker-compose.demo.yml up --build
```

After startup:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`

The frontend also uses the Next.js route handler here and proxies to `api:8000` inside the Docker network.

## 3. Local environment files

### 3.1 `web/.env.local`

Use `web/.env.local.example` as a reference:

```env
NEXT_PUBLIC_API_BASE_URL=
API_PROXY_TARGET=http://127.0.0.1:8000
```

Notes:

- Leave `NEXT_PUBLIC_API_BASE_URL` empty to use same-origin `/api/*`
- `API_PROXY_TARGET` is the actual backend target for the Next.js proxy

### 3.2 `api/.env`

Minimal local config:

```env
DATABASE_URL=sqlite+pysqlite:///./buildflow.db
LLM_PROVIDER=mock
LLM_MODEL=mock-buildflow-v1
LLM_API_MODE=auto
CORS_ALLOW_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

## 4. Validation commands

Run this from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test.ps1
```

Include Playwright if needed:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test.ps1 -IncludeE2E
```
