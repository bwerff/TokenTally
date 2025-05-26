import os
import sys
import json
import pathlib
import subprocess

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"


def test_pricing_cli_compile(tmp_path):
    dsl_path = tmp_path / "rule.dsl"
    dsl_path.write_text("provider=openai\nmodel=gpt-4\ncost=0.01\n")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)
    result = subprocess.run(
        [sys.executable, "-m", "token_tally.pricing_cli", "compile", str(dsl_path)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        check=True,
    )
    data = json.loads(result.stdout)
    assert data["provider"] == "openai"
    assert data["cost"] == 0.01
