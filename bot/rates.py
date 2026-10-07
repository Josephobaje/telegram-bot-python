"""Currency conversion with a pluggable rate provider.

By default the bot uses indicative sample rates (clearly labelled as such).
Set ``RATES_API_URL`` to a JSON endpoint that returns ``{"rates": {"USD": 1, "NGN": 1550, ...}}``
(for example https://open.er-api.com/v6/latest/USD) to use live rates.
"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass

# Indicative USD-based sample rates. Not financial data: replace with a live source.
SAMPLE_RATES: dict[str, float] = {
    "USD": 1.0,
    "NGN": 1550.0,
    "GBP": 0.78,
    "EUR": 0.92,
    "GHS": 15.4,
    "KES": 129.0,
    "ZAR": 18.1,
    "CAD": 1.37,
}

ALIASES = {"NAIRA": "NGN", "N": "NGN", "₦": "NGN", "DOLLAR": "USD", "$": "USD", "POUND": "GBP", "EURO": "EUR"}


class RateError(ValueError):
    pass


def normalize(code: str) -> str:
    c = code.strip().upper()
    return ALIASES.get(c, c)


@dataclass
class RateProvider:
    api_url: str = ""
    cache_seconds: int = 600
    _cache: dict[str, float] | None = None
    _fetched_at: float = 0.0

    @property
    def is_live(self) -> bool:
        return bool(self.api_url)

    def rates(self) -> dict[str, float]:
        if not self.api_url:
            return SAMPLE_RATES
        if self._cache and time.time() - self._fetched_at < self.cache_seconds:
            return self._cache
        with urllib.request.urlopen(self.api_url, timeout=10) as resp:  # noqa: S310 - URL is admin-configured
            data = json.load(resp)
        rates = {k.upper(): float(v) for k, v in data["rates"].items()}
        self._cache, self._fetched_at = rates, time.time()
        return rates

    def convert(self, amount: float, src: str, dst: str) -> float:
        rates = self.rates()
        s, d = normalize(src), normalize(dst)
        for c in (s, d):
            if c not in rates:
                raise RateError(f"Unknown currency '{c}'. Supported: {', '.join(sorted(rates))}")
        if amount < 0:
            raise RateError("Amount must be positive.")
        return amount / rates[s] * rates[d]


def parse_convert_args(args: list[str]) -> tuple[float, str, str]:
    """Accept '/convert 100 usd ngn' or '/convert 100 usd to ngn'."""
    parts = [a for a in args if a.lower() != "to"]
    if len(parts) != 3:
        raise RateError("Usage: /convert <amount> <from> <to>, for example /convert 100 USD NGN")
    try:
        amount = float(parts[0].replace(",", ""))
    except ValueError as exc:
        raise RateError(f"'{parts[0]}' is not a number.") from exc
    return amount, normalize(parts[1]), normalize(parts[2])


def format_money(amount: float, code: str) -> str:
    symbol = {"NGN": "₦", "USD": "$", "GBP": "£", "EUR": "€"}.get(code, "")
    return f"{symbol}{amount:,.2f} {code}" if symbol else f"{amount:,.2f} {code}"
