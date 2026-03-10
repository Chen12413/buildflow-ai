type RouteContext = {
  params: Promise<{ path: string[] }>;
};

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const DEFAULT_PROXY_TARGET = "http://127.0.0.1:8000";
const HOP_BY_HOP_HEADERS = [
  "connection",
  "content-length",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
];

function normalizeProxyTarget(rawTarget?: string): string {
  const target = rawTarget?.trim() || DEFAULT_PROXY_TARGET;
  const withProtocol = /^https?:\/\//i.test(target) ? target : `http://${target}`;
  return withProtocol.replace(/\/+$/, "");
}

async function proxy(request: Request, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(`${normalizeProxyTarget(process.env.API_PROXY_TARGET)}/api/${path.join("/")}`);
  targetUrl.search = incomingUrl.search;

  const headers = new Headers(request.headers);
  for (const header of HOP_BY_HOP_HEADERS) {
    headers.delete(header);
  }
  headers.set("x-forwarded-host", incomingUrl.host);
  headers.set("x-forwarded-proto", incomingUrl.protocol.replace(":", ""));

  const method = request.method.toUpperCase();
  const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();

  try {
    const upstream = await fetch(targetUrl, {
      method,
      headers,
      body: body && body.byteLength > 0 ? body : undefined,
      cache: "no-store",
      redirect: "manual",
    });

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
    return Response.json(
      {
        detail: {
          message: "API proxy unavailable. Please verify API_PROXY_TARGET or backend availability.",
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
