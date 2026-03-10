from fastapi import HTTPException, status


ERROR_MAP: dict[str, tuple[int, str]] = {
    "project_not_found": (status.HTTP_404_NOT_FOUND, "Project not found"),
    "run_not_found": (status.HTTP_404_NOT_FOUND, "Run not found"),
    "artifact_not_found": (status.HTTP_404_NOT_FOUND, "Artifact not found"),
    "prd_artifact_required": (status.HTTP_409_CONFLICT, "A PRD artifact is required before planning generation"),
    "llm_provider_not_supported": (status.HTTP_400_BAD_REQUEST, "Unsupported LLM provider"),
    "llm_api_mode_not_supported": (status.HTTP_400_BAD_REQUEST, "Unsupported LLM API mode"),
    "bailian_api_key_required": (status.HTTP_400_BAD_REQUEST, "DASHSCOPE_API_KEY is required when LLM_PROVIDER=aliyun_bailian"),
    "bailian_dependency_missing": (status.HTTP_500_INTERNAL_SERVER_ERROR, "OpenAI SDK is not installed in the current environment"),
    "bailian_empty_response": (status.HTTP_502_BAD_GATEWAY, "The Bailian provider returned an empty response"),
    "bailian_parse_failed": (status.HTTP_502_BAD_GATEWAY, "The Bailian provider returned content that could not be validated"),
    "bailian_responses_unavailable": (status.HTTP_502_BAD_GATEWAY, "The Bailian Responses API is unavailable for the current request"),
    "bailian_quota_exceeded": (status.HTTP_503_SERVICE_UNAVAILABLE, "Bailian quota exceeded; check billing, quota, or region limits"),
    "bailian_rate_limited": (status.HTTP_429_TOO_MANY_REQUESTS, "Bailian rate limit hit; please retry later"),
    "bailian_auth_failed": (status.HTTP_502_BAD_GATEWAY, "Bailian authentication failed; check DASHSCOPE_API_KEY"),
    "bailian_permission_denied": (status.HTTP_502_BAD_GATEWAY, "Bailian denied the request for the configured account"),
    "bailian_bad_request": (status.HTTP_502_BAD_GATEWAY, "Bailian rejected the request payload"),
    "bailian_request_failed": (status.HTTP_502_BAD_GATEWAY, "Bailian request failed due to network or upstream error"),
}


def raise_http_error(code: str) -> None:
    http_status, message = ERROR_MAP.get(code, (status.HTTP_400_BAD_REQUEST, code))
    raise HTTPException(status_code=http_status, detail={"code": code, "message": message, "details": None})