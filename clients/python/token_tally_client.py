import requests


class TokenTallyClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def get_usage(self):
        resp = requests.get(f"{self.base_url}/api/trpc/usage")
        resp.raise_for_status()
        return resp.json().get('result', {}).get('data', [])
