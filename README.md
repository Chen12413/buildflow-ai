# BuildFlow AI

![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?logo=fastapi&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-E2E-2EAD33?logo=playwright&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![CI Ready](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-BuildFlow%20AI-4f46e5?logo=render&logoColor=white)](https://chen12413-buildflow-web.onrender.com)
[![API Health](https://img.shields.io/badge/API-Healthy-10b981?logo=fastapi&logoColor=white)](https://chen12413-buildflow-api.onrender.com/health)
[![GitHub Repo](https://img.shields.io/badge/GitHub-buildflow--ai-111827?logo=github&logoColor=white)](https://github.com/Chen12413/buildflow-ai)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Chen12413/buildflow-ai)

BuildFlow AI is an AI agent workflow project built with `Next.js + FastAPI`. It turns rough product ideas into clarification notes, PRD output, implementation planning, task breakdown, and a multi-agent demo blueprint through one maintainable end-to-end flow.

> Main flow: `Idea Input -> Clarification -> PRD -> Planning -> Task Breakdown -> Demo -> Export`

## Live URLs

- Web demo: `https://chen12413-buildflow-web.onrender.com`
- API base: `https://chen12413-buildflow-api.onrender.com`
- Health check: `https://chen12413-buildflow-api.onrender.com/health`

> The live deployment uses the `mock` provider by default, so the full main flow can be tested without any API key.

## Why this project matters

This is not a throwaway vibe-coding prototype. It is a long-term portfolio project focused on business completeness and engineering maintainability.

- Designed for AI product managers, indie builders, and startup teams
- Demonstrates how LLM capability can be embedded into a practical workflow
- Focuses on PRD-driven development, module boundaries, testing, iteration, and showcase quality
- Suitable for GitHub, personal website, and resume presentation

## Core capabilities

- Capture a product idea and create a structured project card
- Generate clarification questions automatically
- Turn clarified inputs into a PRD
- Turn the PRD into an implementation plan
- Break the plan down into module-level tasks and test checkpoints
- Generate a multi-agent demo blueprint with screens, flows, and agent cards
- Present long-running stages with polished status panels and progress bars
- Export results as Markdown
- Switch between `mock` and real LLM providers
- Support Aliyun Bailian with responses-first and chat fallback strategy
- Handle transient provider failures with friendlier errors and demo fallback behavior
- Cover the flow with backend tests, frontend build checks, and Playwright E2E

## Showcase highlights

- **Real workflow**: not a single feature, but a full agent business chain
- **Maintainable engineering**: API design, structure, scripts, tests, and deployment are all included
- **Provider flexibility**: demo-friendly `mock` mode and real-provider mode both exist
- **Presentation quality**: progress feedback, demo studio, and agent panels are ready for portfolio use
- **Resilience**: real-provider mode includes responses-first routing, fallback paths, and clearer error messages
- **Publish-ready**: includes `render.yaml`, Docker, CI, and a public live demo

## Latest improvements

- Added `Task Breakdown` and `Demo` stages to extend the chain beyond PRD and planning
- Added a multi-agent demo studio with screen-level outputs and agent responsibility cards
- Improved long-task UX with a reusable `StatusPanel` and animated percentage progress bar
- Improved Bailian integration with better timeout handling, retry strategy, and user-friendly error mapping
- Added more regression coverage around provider fallback and demo generation behavior

## Portfolio kit

- Case study: `docs/portfolio-case-study.md`
- Resume / homepage copy: `docs/profile-copy.md`
- Showcase guide: `docs/showcase-kit.md`
- Social preview cover: `docs/assets/social-preview.svg`

## Screenshots

| Home | New Project |
|---|---|
| ![BuildFlow AI Home](docs/assets/screenshots/home.png) | ![BuildFlow AI New Project](docs/assets/screenshots/new-project.png) |

| Clarification | PRD |
|---|---|
| ![BuildFlow AI Clarification](docs/assets/screenshots/clarification.png) | ![BuildFlow AI PRD](docs/assets/screenshots/prd.png) |

| Planning |
|---|
| ![BuildFlow AI Planning](docs/assets/screenshots/planning.png) |

| Task Breakdown | Demo Overview |
|---|---|
| ![BuildFlow AI Task Breakdown](docs/assets/screenshots/task-breakdown.png) | ![BuildFlow AI Demo Overview](docs/assets/screenshots/demo-overview.png) |

| Demo Studio | Agent Panel |
|---|---|
| ![BuildFlow AI Demo Studio](docs/assets/screenshots/demo-studio.png) | ![BuildFlow AI Agent Panel](docs/assets/screenshots/agent-panel.png) |

## Architecture

```mermaid
flowchart LR
  U[User] --> W[Next.js Web]
  W --> P[Next.js API Proxy]
  P --> A[FastAPI API]
  A --> D[(SQLite)]
  A --> L[LLM Provider\nMock / Aliyun Bailian]
  A --> C1[Clarification Service]
  A --> C2[PRD Service]
  A --> C3[Planning Service]
  A --> C4[Task Breakdown Service]
  A --> C5[Demo Service]
  A --> E[Export Service]
  C1 --> L
  C2 --> L
  C3 --> L
  C4 --> L
  C5 --> L
  C1 --> D
  C2 --> D
  C3 --> D
  C4 --> D
  C5 --> D
  E --> D
```

## Tech stack

### Frontend
- `Next.js 15`
- `React 19`
- `TypeScript`
- `Tailwind CSS`

### Backend
- `FastAPI`
- `SQLAlchemy`
- `Pydantic Settings`
- `SQLite`

### Engineering
- `pytest`
- `Playwright`
- `GitHub Actions`
- `Docker`
- `PowerShell` scripts for dev and test workflows
- Stable web workspace sync for OneDrive-heavy Windows setups

## Quick start

### Local development

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
```

If your repo is inside `OneDrive` and Next.js becomes unstable, use the stable web copy mode:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1 -UseStableWebCopy
```

Default local URLs:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`

### Production preview for web

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\web-preview.ps1
```

Only build without starting preview:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\web-preview.ps1 -BuildOnly
```

### Auto-generate showcase screenshots

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\showcase.ps1
```

If your repo is inside `OneDrive`, the screenshot flow can also use the stable web copy automatically. You can force it explicitly with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\showcase.ps1 -UseStableWebCopy
```

### Run tests

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test.ps1
```

Include E2E:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test.ps1 -IncludeE2E
```

### Verification snapshot

- `scripts/test.ps1` validates backend tests and frontend build checks
- `scripts/e2e.ps1` validates the end-to-end flow from idea input to demo
- `scripts/showcase.ps1` generates portfolio screenshots automatically
- `scripts/web-preview.ps1` builds and serves a production-style preview outside OneDrive
- Real-provider mode has been smoke-tested locally with Bailian across the full chain when provider quota and request stability allow

## Environment setup

### `api/.env`

Minimal mock configuration:

```env
DATABASE_URL=sqlite+pysqlite:///./buildflow.db
LLM_PROVIDER=mock
LLM_MODEL=mock-buildflow-v1
LLM_API_MODE=auto
CORS_ALLOW_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

Switch to Aliyun Bailian:

```env
LLM_PROVIDER=aliyun_bailian
LLM_MODEL=qwen3.5-plus
LLM_API_MODE=auto
DASHSCOPE_API_KEY=<your-bailian-api-key>
DASHSCOPE_CHAT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_RESPONSES_BASE_URL=https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1
```

### `web/.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=
API_PROXY_TARGET=http://127.0.0.1:8000
```

Notes:

- Leave `NEXT_PUBLIC_API_BASE_URL` empty to use same-origin `/api/*`
- `API_PROXY_TARGET` points the Next.js server-side proxy to the real backend

## Deployment

### Recommended: Render Blueprint

This repo includes `render.yaml` and has already been validated with a live deployment.

It creates two free public services:

- `chen12413-buildflow-api` as a public web service
- `chen12413-buildflow-web` as a public web service

The frontend keeps using same-origin `/api/*`, and the Next.js route handler forwards requests to the backend public URL. The backend URL is injected automatically through Render `fromService.envVarKey: RENDER_EXTERNAL_URL`.

See `docs/deployment.md` for details.

## Project structure

```text
api/                 FastAPI backend
web/                 Next.js frontend
docs/                PRD, deployment, assets, and profile copy
scripts/             Dev, test, E2E, and showcase scripts
render.yaml          Render Blueprint configuration
```

## Roadmap

- [x] Single-flow MVP: Idea -> Clarification -> PRD -> Planning
- [x] Task breakdown and demo generation stages
- [x] Multi-agent demo studio and agent panels
- [x] `mock` provider and real provider modes
- [x] Aliyun Bailian integration
- [x] Backend tests and frontend build checks
- [x] Playwright E2E
- [x] GitHub-ready repository polish
- [x] Render live deployment
- [x] Long-task UX polish and progress feedback
- [ ] Postgres persistence upgrade
- [ ] Team collaboration and history comparison
- [ ] Prompt debugging and evaluation panel

## License

MIT License. See `LICENSE`.
