# TokenTally Gateway Worker

This Cloudflare Worker acts as the edge proxy for TokenTally.
It forwards requests to the provider specified in the `X-LLM-Provider`
header and enforces per-API-key concurrency and rate limits.

## Configuration

Limits can be supplied globally via environment variables or overridden per API
key using a KV namespace or an environment variable containing JSON.

| Variable | Description |
| -------- | ----------- |
| `CONCURRENCY_LIMIT` | Default concurrent requests allowed per API key (default `5`) |
| `RATE_LIMIT` | Default requests per minute allowed per API key (default `60`) |
| `KEY_LIMITS_JSON` | Optional JSON object mapping API keys to `{ "concurrency": n, "rate": m }` |
| `KEY_LIMITS` | Optional KV namespace for per-key limit objects |

Values found in `KEY_LIMITS_JSON` or `KEY_LIMITS` override the defaults for the
matching API key. A limit value of `0` means no limit for that field.

## Development

```bash
npm install
npm run start
```

The worker expects an `Authorization` header containing the caller's API key.
Requests exceeding the configured limits receive `HTTP 429` responses.
