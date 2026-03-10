# E2E 自动化测试

## 目标
- 覆盖 BuildFlow AI 当前唯一主链路：`Idea Input -> Clarification -> PRD -> Planning -> Export`
- 使用 `mock` Provider 保证自动化可重复、低成本、无外部额度依赖
- 为后续版本迭代提供稳定回归基线

## 技术方案
- 测试框架：`Playwright`
- 浏览器：`Chromium`
- 服务启动：根目录脚本 `scripts/e2e.ps1`
- 后端模式：`LLM_PROVIDER=mock`
- 测试数据库：`api/buildflow.e2e.db`

## 运行方式
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\e2e.ps1
```

首次安装依赖时可执行：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\e2e.ps1 -InstallDeps
```

需要观察真实浏览器窗口时可执行：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\e2e.ps1 -Headed
```

## 当前覆盖点
- 首页进入创建项目
- 新建项目表单填写与提交
- 澄清问题生成与回答提交
- PRD 页面轮询完成与结果展示
- PRD Markdown 导出
- Planning 页面轮询完成与结果展示
- Planning Markdown 导出

## 产物位置
- 运行日志：`output/e2e/`
- Playwright HTML 报告：`web/playwright-report/`
- 失败截图、trace、video：`web/test-results/`
