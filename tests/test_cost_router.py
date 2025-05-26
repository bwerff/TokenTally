import sys
import pathlib
from datetime import datetime

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "src"))

import pytest

from token_tally.markup import MarkupRuleStore
from token_tally.fx_rates import store_rates
from token_tally.cost_router import route_request


def test_route_request_cheapest(tmp_path):
    markup_db = tmp_path / "rules.db"
    store = MarkupRuleStore(str(markup_db))
    store.create_rule("r1", "openai", "gpt-4", 0.2, "2024-01-01")
    store.create_rule("r2", "cohere", "gpt-4", 0.0, "2024-01-01")

    fx_db = tmp_path / "fx.db"
    store_rates({"EUR": 1.0, "USD": 1.2}, fetch_date="2024-06-01", db_path=str(fx_db))

    options = [
        {"provider": "openai", "model": "gpt-4", "unit_cost": 0.02, "currency": "USD"},
        {"provider": "cohere", "model": "gpt-4", "unit_cost": 0.018, "currency": "EUR"},
    ]
    result = route_request(
        options,
        "gpt-4",
        ts=datetime(2024, 6, 1),
        markup_db_path=str(markup_db),
        fx_db_path=str(fx_db),
    )
    assert result["provider"] == "cohere"
    assert round(result["final_cost"], 6) == round(0.018 * 1.2, 6)


def test_route_request_no_options():
    with pytest.raises(ValueError):
        route_request([], "gpt")
