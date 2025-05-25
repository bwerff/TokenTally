# TokenTally Python Client

This helper fetches usage records from a TokenTally deployment.

```python
from token_tally_client import TokenTallyClient
client = TokenTallyClient("https://example.com")
usage = client.get_usage()
```

## Retry behaviour

`get_usage()` retries failed requests up to three times with exponential backoff.
