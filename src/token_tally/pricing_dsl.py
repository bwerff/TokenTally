"""Parse pricing DSL into markup rule dictionaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List
import re


@dataclass
class MarkupRule:
    """A parsed markup rule."""

    id: str
    provider: str
    model: str
    markup: float
    effective_date: str


_RULE_RE = re.compile(
    r"^(?P<provider>[\w\-./]+)\s+"  # provider
    r"(?P<model>[\w\-./]+)\s+"  # model
    r"(?P<markup>[\d.]+%?)\s+"  # markup or percentage
    r"(?P<date>\d{4}-\d{2}-\d{2})$"  # date
)


def _parse_markup(value: str) -> float:
    if value.endswith("%"):
        return float(value[:-1]) / 100
    return float(value)


def parse_pricing_dsl(text: str) -> List[dict]:
    """Parse DSL text into a list of markup rule dictionaries."""

    rules: List[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _RULE_RE.match(line)
        if not m:
            raise ValueError(f"Invalid DSL line: {line}")
        provider = m.group("provider")
        model = m.group("model")
        markup = _parse_markup(m.group("markup"))
        date = m.group("date")
        rule_id = f"{provider}-{model}-{date}"
        rules.append(
            {
                "id": rule_id,
                "provider": provider,
                "model": model,
                "markup": markup,
                "effective_date": date,
            }
        )
    return rules
