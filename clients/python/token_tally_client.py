import json
import time
from typing import Any, List

from urllib import request, error


class TokenTallyClient:
    def __init__(self, base_url: str, retries: int = 3, backoff: float = 0.1):
        self.base_url = base_url.rstrip("/")
        self.retries = retries
        self.backoff = backoff

    def get_usage(self) -> List[Any]:
        delay = self.backoff
        for attempt in range(self.retries):
            try:
                with request.urlopen(f"{self.base_url}/api/trpc/usage") as resp:
                    if resp.status != 200:
                        raise error.HTTPError(
                            resp.url, resp.status, resp.reason, resp.headers, None
                        )
                    body = json.loads(resp.read())
                    return body.get("result", {}).get("data", [])
            except Exception:
                if attempt == self.retries - 1:
                    raise
                time.sleep(delay)
                delay *= 2
