from fastapi import HTTPException, status


ERROR_MAP: dict[str, tuple[int, str]] = {
    "project_not_found": (status.HTTP_404_NOT_FOUND, "Project not found"),
    "run_not_found": (status.HTTP_404_NOT_FOUND, "Run not found"),
    "artifact_not_found": (status.HTTP_404_NOT_FOUND, "Artifact not found"),
    "prd_artifact_required": (status.HTTP_409_CONFLICT, "A PRD artifact is required before planning generation"),
    "planning_artifact_required": (status.HTTP_409_CONFLICT, "A planning artifact is required before task breakdown generation"),
    "task_breakdown_artifact_required": (status.HTTP_409_CONFLICT, "A task breakdown artifact is required before demo generation"),
    "llm_provider_not_supported": (status.HTTP_400_BAD_REQUEST, "Unsupported LLM provider"),
    "llm_api_mode_not_supported": (status.HTTP_400_BAD_REQUEST, "Unsupported LLM API mode"),
    "bailian_api_key_required": (status.HTTP_400_BAD_REQUEST, "缺少百炼 API Key：请先配置 DASHSCOPE_API_KEY。"),
    "bailian_dependency_missing": (status.HTTP_500_INTERNAL_SERVER_ERROR, "当前环境缺少 OpenAI SDK，无法调用百炼兼容接口。"),
    "bailian_empty_response": (status.HTTP_502_BAD_GATEWAY, "百炼返回了空结果，请稍后重试。"),
    "bailian_parse_failed": (status.HTTP_502_BAD_GATEWAY, "百炼返回内容无法稳定解析，系统可稍后重试或降级兜底生成。"),
    "bailian_responses_unavailable": (status.HTTP_502_BAD_GATEWAY, "百炼 Responses 接口当前不可用，系统将尝试兼容后备方式。"),
    "bailian_quota_exceeded": (status.HTTP_503_SERVICE_UNAVAILABLE, "百炼额度或配额不足，请先检查账户余额、配额或地域限制。"),
    "bailian_rate_limited": (status.HTTP_429_TOO_MANY_REQUESTS, "百炼当前请求过多，请稍后再试。"),
    "bailian_auth_failed": (status.HTTP_502_BAD_GATEWAY, "百炼鉴权失败，请检查 DASHSCOPE_API_KEY 是否正确。"),
    "bailian_permission_denied": (status.HTTP_502_BAD_GATEWAY, "当前百炼账号没有权限执行该请求。"),
    "bailian_bad_request": (status.HTTP_502_BAD_GATEWAY, "百炼拒绝了本次请求，请检查模型、参数或请求内容。"),
    "bailian_timeout": (status.HTTP_504_GATEWAY_TIMEOUT, "百炼响应超时，系统已尽量自动重试；如果连续失败，可稍后重试。"),
    "bailian_request_failed": (status.HTTP_502_BAD_GATEWAY, "百炼服务暂时不可用或网络抖动，本次请求未成功完成。"),
}


def raise_http_error(code: str) -> None:
    http_status, message = ERROR_MAP.get(code, (status.HTTP_400_BAD_REQUEST, code))
    raise HTTPException(status_code=http_status, detail={"code": code, "message": message, "details": None})