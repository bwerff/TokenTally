export interface Env {
  CREDIT_LIMIT?: string;
  WEBHOOK_URL?: string;
}

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
const spendTotals = new Map<string, number>();
const alerted = new Set<string>();

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

async function sendAlert(env: Env, msg: string): Promise<void> {
  if (!env.WEBHOOK_URL) return;
  await fetch(env.WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: msg }),
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
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

    const creditLimit = parseFloat(env.CREDIT_LIMIT || '0');
    const spent = spendTotals.get(apiKey) || 0;
    if (creditLimit > 0 && spent >= creditLimit) {
      await sendAlert(env, `API key ${apiKey} exceeded credit limit`);
      exitConcurrency(apiKey);
      return new Response('Credit limit exceeded', { status: 429 });
    }

    const url = new URL(request.url);
    const targetUrl = base + url.pathname + url.search;
    const proxyReq = new Request(targetUrl, request);
    proxyReq.headers.delete('X-LLM-Provider');

    try {
      const resp = await fetch(proxyReq);
      const cost = parseFloat(resp.headers.get('X-Usage-Cost') || '0');
      if (creditLimit > 0 && cost > 0) {
        const newTotal = spent + cost;
        spendTotals.set(apiKey, newTotal);
        if (newTotal >= creditLimit && !alerted.has(apiKey)) {
          alerted.add(apiKey);
          await sendAlert(env, `API key ${apiKey} hit credit limit`);
        }
      }
      return resp;
    } finally {
      exitConcurrency(apiKey);
    }
  },
};
