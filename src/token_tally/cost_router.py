from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Iterable, Optional, Dict, Any
import os

from .gpu_arbitrage import choose_best_gpu_host

from .markup import get_effective_markup
from .fx_rates import get_rates
from .fx import convert


@dataclass
class ProviderOption:
    provider: str
    model: str
    unit_cost: float
    currency: str = "USD"
    extra: Dict[str, Any] | None = None


def _final_cost(
    option: ProviderOption,
    ts: datetime,
    rates: Dict[str, float],
    markup_db_path: str,
    target_currency: str,
) -> float:
    rule = get_effective_markup(
        option.provider, option.model, ts.isoformat(), db_path=markup_db_path
    )
    markup = rule["markup"] if rule else 0.0
    cost = option.unit_cost * (1 + markup)
    if option.currency != target_currency and rates:
        cost = convert(cost, option.currency, target_currency, rates)
    return cost


def route_request(
    options: Iterable[Dict[str, Any]] | Iterable[ProviderOption],
    model: str,
    *,
    ts: Optional[datetime] = None,
    markup_db_path: str = "markup_rules.db",
    fx_db_path: str = "fx_rates.db",
    target_currency: str = "USD",
) -> Dict[str, Any]:
    """Return provider option with the lowest cost.

    ``options`` is an iterable of provider descriptions. Each must include
    ``provider``, ``model`` and ``unit_cost`` fields and may include a
    ``currency`` field (default ``USD``). The returned dict includes a
    ``final_cost`` key with the computed price in ``target_currency``.
    """

    opts: list[ProviderOption] = []
    for o in options:
        if isinstance(o, ProviderOption):
            opts.append(o)
        else:
            opts.append(
                ProviderOption(
                    provider=o["provider"],
                    model=o.get("model", model),
                    unit_cost=o["unit_cost"],
                    currency=o.get("currency", "USD"),
                    extra={
                        k: v
                        for k, v in o.items()
                        if k not in {"provider", "model", "unit_cost", "currency"}
                    },
                )
            )

    if not opts:
        raise ValueError("no provider options")

    ts = ts or datetime.now(UTC)
    rates = get_rates(db_path=fx_db_path)

    best: Optional[ProviderOption] = None
    best_cost = float("inf")
    for opt in opts:
        cost = _final_cost(opt, ts, rates, markup_db_path, target_currency)
        if cost < best_cost:
            best = opt
            best_cost = cost
    if best is None:
        raise ValueError("no provider options")
    result = {
        "provider": best.provider,
        "model": best.model,
        "unit_cost": best.unit_cost,
        "currency": best.currency,
        "final_cost": best_cost,
    }
    if best.extra:
        result.update(best.extra)
    return result


PROVIDER_BASE = {
    "openai": os.environ.get("OPENAI_BASE", "https://api.openai.com/v1"),
    "anthropic": os.environ.get("ANTHROPIC_BASE", "https://api.anthropic.com"),
    "cohere": os.environ.get("COHERE_BASE", "https://api.cohere.ai"),
}


def route_provider(provider: str, model: str | None = None) -> str:
    """Return the base URL for ``provider``."""

    key = provider.lower()
    if key in {"local", "ollama"}:
        return choose_best_gpu_host()
    base = PROVIDER_BASE.get(key)
    if base is None:
        raise ValueError(f"unknown provider: {provider}")
    return base


__all__ = ["route_request", "route_provider"]
