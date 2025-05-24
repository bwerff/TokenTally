# TokenTally Gateway Worker

This Cloudflare Worker acts as the edge proxy for TokenTally.
It forwards requests to the provider specified in the `X-LLM-Provider`
header and enforces per-API-key concurrency and rate limits.

## Development

```bash
npm install
npm run start
```

The worker expects an `Authorization` header containing the caller's API key.
Requests exceeding the configured limits receive `HTTP 429` responses.
