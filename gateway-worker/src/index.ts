export interface Env {
  CREDIT_LIMIT?: string;
  WEBHOOK_URL?: string;
  CONCURRENCY_LIMIT?: string;
  RATE_LIMIT?: string;
  KEY_LIMITS?: KVNamespace;
  KEY_LIMITS_JSON?: string;
}

const PROVIDER_BASE: Record<string, string> = {
  openai: 'https://api.openai.com',
  anthropic: 'https://api.anthropic.com',
};

const DEFAULT_CONCURRENCY_LIMIT = 5;
const DEFAULT_RATE_LIMIT = 60; // requests per minute
const WINDOW_MS = 60_000;

const concurrency = new Map<string, number>();
interface Bucket { tokens: number; last: number; }
const buckets = new Map<string, Bucket>();
const spendTotals = new Map<string, number>();
const alerted = new Set<string>();

let envLimitCache: Record<string, { concurrency?: number; rate?: number }> | null = null;

function getEnvLimits(env: Env): Record<string, { concurrency?: number; rate?: number }> {
  if (envLimitCache === null) {
    try {
      envLimitCache = env.KEY_LIMITS_JSON ? JSON.parse(env.KEY_LIMITS_JSON) : {};
    } catch {
      envLimitCache = {};
    }
  }
  return envLimitCache;
}

async function getLimits(env: Env, key: string): Promise<{ concurrency: number; rate: number }> {
  const defaults = {
    concurrency: parseInt(env.CONCURRENCY_LIMIT || String(DEFAULT_CONCURRENCY_LIMIT), 10),
    rate: parseInt(env.RATE_LIMIT || String(DEFAULT_RATE_LIMIT), 10),
  };

  const envLimits = getEnvLimits(env)[key];
  if (envLimits) {
    return {
      concurrency: envLimits.concurrency ?? defaults.concurrency,
      rate: envLimits.rate ?? defaults.rate,
    };
  }

  if (env.KEY_LIMITS) {
    const kvLimits = await env.KEY_LIMITS.get(key, 'json') as { concurrency?: number; rate?: number } | null;
    if (kvLimits) {
      return {
        concurrency: kvLimits.concurrency ?? defaults.concurrency,
        rate: kvLimits.rate ?? defaults.rate,
      };
    }
  }

  return defaults;
}

function enterConcurrency(key: string, limit: number): boolean {
  const current = concurrency.get(key) || 0;
  if (current >= limit) return false;
  concurrency.set(key, current + 1);
  return true;
}

function exitConcurrency(key: string): void {
  const current = concurrency.get(key) || 1;
  concurrency.set(key, current - 1);
}

function allowRequest(key: string, limit: number): boolean {
  const now = Date.now();
  const bucket = buckets.get(key) || { tokens: limit, last: now };
  const elapsed = now - bucket.last;
  bucket.tokens = Math.min(limit, bucket.tokens + (elapsed * limit) / WINDOW_MS);
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

    const limits = await getLimits(env, apiKey);

    if (!enterConcurrency(apiKey, limits.concurrency)) {
      return new Response('Concurrency limit exceeded', { status: 429 });
    }
    if (!allowRequest(apiKey, limits.rate)) {
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
