type RouteContext = {
  params: Promise<{ path: string[] }>;
};

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const DEFAULT_PROXY_TARGET = "http://127.0.0.1:8000";
const MAX_PROXY_ATTEMPTS = 2;
const PROXY_RETRY_DELAY_MS = 1200;
const DEFAULT_PROXY_TIMEOUT_MS = 90000;
const PROXY_TIMEOUT_MS = (() => {
  const configuredTimeout = Number(process.env.API_PROXY_TIMEOUT_MS ?? DEFAULT_PROXY_TIMEOUT_MS);
  return Number.isFinite(configuredTimeout) && configuredTimeout > 0 ? configuredTimeout : DEFAULT_PROXY_TIMEOUT_MS;
})();
const HOP_BY_HOP_HEADERS = [
  "connection",
  "content-length",
  "expect",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
];
const RETRYABLE_STATUS_CODES = new Set([502, 503, 504]);

function normalizeProxyTarget(rawTarget?: string): string {
  const target = rawTarget?.trim() || DEFAULT_PROXY_TARGET;
  const withProtocol = /^https?:\/\//i.test(target) ? target : `http://${target}`;
  return withProtocol.replace(/\/+$/, "");
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function buildProxyUnavailableMessage(): string {
  return "\u540e\u7aef\u670d\u52a1\u6b63\u5728\u5524\u9192\u6216\u77ed\u6682\u4e0d\u53ef\u7528\uff0c\u8bf7\u7b49\u5f85 30-60 \u79d2\u540e\u91cd\u8bd5\u3002";
}

function formatProxyError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return String(error);
}

async function wakeUpProxyTarget(proxyTarget: string): Promise<void> {
  try {
    await fetch(new URL(`${proxyTarget}/health`), {
      cache: "no-store",
      redirect: "manual",
    });
  } catch {
    return;
  }
}

async function fetchWithTimeout(input: URL, init: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), PROXY_TIMEOUT_MS);

  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

async function proxy(request: Request, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const incomingUrl = new URL(request.url);
  const proxyTarget = normalizeProxyTarget(process.env.API_PROXY_TARGET);
  const targetUrl = new URL(`${proxyTarget}/api/${path.join("/")}`);
  targetUrl.search = incomingUrl.search;

  const headers = new Headers(request.headers);
  for (const header of HOP_BY_HOP_HEADERS) {
    headers.delete(header);
  }
  headers.set("x-forwarded-host", incomingUrl.host);
  headers.set("x-forwarded-proto", incomingUrl.protocol.replace(":", ""));

  const method = request.method.toUpperCase();
  const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();
  const requestInit: RequestInit = {
    method,
    headers,
    body: body && body.byteLength > 0 ? body : undefined,
    cache: "no-store",
    redirect: "manual",
  };

  try {
    let upstream: Response | null = null;

    for (let attempt = 1; attempt <= MAX_PROXY_ATTEMPTS; attempt += 1) {
      try {
        upstream = await fetchWithTimeout(targetUrl, requestInit);
      } catch (error) {
        if (attempt === MAX_PROXY_ATTEMPTS) {
          throw error;
        }

        console.warn(`API proxy request failed before receiving an upstream response. Retrying attempt ${attempt + 1}/${MAX_PROXY_ATTEMPTS}.`, error);
        await wakeUpProxyTarget(proxyTarget);
        await sleep(PROXY_RETRY_DELAY_MS * attempt);
        continue;
      }

      if (!RETRYABLE_STATUS_CODES.has(upstream.status) || attempt === MAX_PROXY_ATTEMPTS) {
        break;
      }

      console.warn(`API proxy received ${upstream.status} from upstream. Retrying attempt ${attempt + 1}/${MAX_PROXY_ATTEMPTS}.`);
      await wakeUpProxyTarget(proxyTarget);
      await sleep(PROXY_RETRY_DELAY_MS * attempt);
    }

    if (!upstream) {
      throw new Error("Upstream response missing");
    }

    const responseHeaders = new Headers(upstream.headers);
    for (const header of HOP_BY_HOP_HEADERS) {
      responseHeaders.delete(header);
    }

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error("API proxy request failed", error);
    const shouldExposeCause = process.env.BUILD_FLOW_DEBUG_PROXY === "1";
    return Response.json(
      {
        detail: {
          message: buildProxyUnavailableMessage(),
          ...(shouldExposeCause ? { cause: formatProxyError(error) } : {}),
        },
      },
      { status: 502 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
export const HEAD = proxy;
