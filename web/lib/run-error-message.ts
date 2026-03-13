const RUN_ERROR_MESSAGES: Record<string, string> = {
  bailian_timeout: "百炼响应超时，本次生成未能按时完成。系统已经尽量自动重试；如果连续失败，请稍后再试。",
  bailian_request_failed: "百炼服务暂时不可用或网络抖动，本次生成未成功完成，请稍后重试。",
  bailian_responses_unavailable: "百炼 Responses 接口暂时不可用，系统已尝试兼容后备方式。",
  bailian_parse_failed: "百炼返回内容不够稳定，系统未能完成结构化解析，请稍后重试。",
  bailian_quota_exceeded: "百炼额度或配额不足，请先检查账户余额、配额或地域限制。",
  bailian_rate_limited: "百炼当前请求过多，请稍后再试。",
  bailian_auth_failed: "百炼鉴权失败，请检查 DASHSCOPE_API_KEY 是否正确。",
  bailian_permission_denied: "当前百炼账号没有权限执行该请求。",
  bailian_bad_request: "百炼拒绝了本次请求，请检查模型、参数或请求内容。",
};

export function formatRunErrorMessage(message: string | null | undefined, fallback: string): string {
  const normalized = message?.trim();
  if (!normalized) {
    return fallback;
  }

  return RUN_ERROR_MESSAGES[normalized] ?? normalized;
}