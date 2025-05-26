import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "tests" / "load_nextauth.mjs"
CONFIG = ROOT / "frontend" / "pages" / "api" / "auth" / "[...nextauth].ts"


def load_config(extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        ["node", "--experimental-vm-modules", LOADER, str(CONFIG)],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return json.loads(result.stdout)


def test_load_default():
    cfg = load_config()
    assert any(p["id"] == "credentials" for p in cfg["providers"])


def test_load_google():
    cfg = load_config({"GOOGLE_CLIENT_ID": "id", "GOOGLE_CLIENT_SECRET": "sec"})
    ids = [p["id"] for p in cfg["providers"]]
    assert "google" in ids


def test_load_okta():
    cfg = load_config({"OKTA_CLIENT_ID": "id", "OKTA_CLIENT_SECRET": "sec"})
    ids = [p["id"] for p in cfg["providers"]]
    assert "okta" in ids


def test_load_saml():
    cfg = load_config(
        {"SAML_ENTRYPOINT": "url", "SAML_ISSUER": "iss", "SAML_CERT": "cert"}
    )
    ids = [p["id"] for p in cfg["providers"]]
    assert "saml" in ids
