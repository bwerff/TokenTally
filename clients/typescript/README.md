# TokenTally TypeScript Client

Fetch usage data from a TokenTally server.

```ts
import { getUsage } from './index.js';
const usage = await getUsage('https://example.com');
```

## Retry behaviour

`getUsage()` retries transient errors up to three times with exponential backoff.
