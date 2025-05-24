export interface Env {}

const PROVIDER_BASE: Record<string, string> = {
  openai: 'https://api.openai.com',
  anthropic: 'https://api.anthropic.com',
};

const CONCURRENCY_LIMIT = 5;
const RATE_LIMIT = 60; // requests per minute
const WINDOW_MS = 60_000;

const concurrency = new Map<string, number>();
interface Bucket { tokens: number; last: number; }
const buckets = new Map<string, Bucket>();

function enterConcurrency(key: string): boolean {
  const current = concurrency.get(key) || 0;
  if (current >= CONCURRENCY_LIMIT) return false;
  concurrency.set(key, current + 1);
  return true;
}

function exitConcurrency(key: string): void {
  const current = concurrency.get(key) || 1;
  concurrency.set(key, current - 1);
}

function allowRequest(key: string): boolean {
  const now = Date.now();
  const bucket = buckets.get(key) || { tokens: RATE_LIMIT, last: now };
  const elapsed = now - bucket.last;
  bucket.tokens = Math.min(RATE_LIMIT, bucket.tokens + elapsed * RATE_LIMIT / WINDOW_MS);
  bucket.last = now;
  if (bucket.tokens < 1) {
    buckets.set(key, bucket);
    return false;
  }
  bucket.tokens -= 1;
  buckets.set(key, bucket);
  return true;
}

export default {
  async fetch(request: Request): Promise<Response> {
    const apiKey = request.headers.get('Authorization');
    if (!apiKey) {
      return new Response('Missing Authorization header', { status: 401 });
    }

    if (!enterConcurrency(apiKey)) {
      return new Response('Concurrency limit exceeded', { status: 429 });
    }
    if (!allowRequest(apiKey)) {
      exitConcurrency(apiKey);
      return new Response('Rate limit exceeded', { status: 429 });
    }

    const provider = request.headers.get('X-LLM-Provider') || 'openai';
    const base = PROVIDER_BASE[provider.toLowerCase()];
    if (!base) {
      exitConcurrency(apiKey);
      return new Response('Unknown provider', { status: 400 });
    }

    const url = new URL(request.url);
    const targetUrl = base + url.pathname + url.search;
    const proxyReq = new Request(targetUrl, request);
    proxyReq.headers.delete('X-LLM-Provider');

    try {
      const resp = await fetch(proxyReq);
      return resp;
    } finally {
      exitConcurrency(apiKey);
    }
  },
};
