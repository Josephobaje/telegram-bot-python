from pathlib import Path

import pytest

from bot.faq import best_answer, load_faq
from bot.rates import RateError, RateProvider, format_money, parse_convert_args
from bot.reminders import ReminderError, humanize, parse_duration, parse_reminder

FAQ = load_faq(Path(__file__).resolve().parents[1] / "bot" / "faq.json")


@pytest.mark.parametrize("value,seconds", [("30s", 30), ("10m", 600), ("1h30m", 5400), ("2d", 172800), ("1H", 3600)])
def test_parse_duration(value, seconds):
    assert parse_duration(value) == seconds


@pytest.mark.parametrize("value", ["", "abc", "10", "0m", "31d", "5x"])
def test_parse_duration_invalid(value):
    with pytest.raises(ReminderError):
        parse_duration(value)


def test_parse_reminder():
    r = parse_reminder(["15m", "Send", "the", "invoice"])
    assert r.seconds == 900 and r.text == "Send the invoice"
    with pytest.raises(ReminderError):
        parse_reminder(["15m"])


def test_humanize():
    assert humanize(5400) == "1 hour 30 minutes"
    assert humanize(1) == "1 second"


def test_convert_sample_rates():
    p = RateProvider()
    assert p.convert(1, "USD", "NGN") == 1550.0
    assert p.convert(1550, "naira", "dollar") == pytest.approx(1.0)
    with pytest.raises(RateError):
        p.convert(1, "USD", "XYZ")


def test_parse_convert_args():
    assert parse_convert_args(["1,000", "usd", "to", "ngn"]) == (1000.0, "USD", "NGN")
    with pytest.raises(RateError):
        parse_convert_args(["ten", "usd", "ngn"])
    with pytest.raises(RateError):
        parse_convert_args(["10", "usd"])


def test_live_provider_uses_api(monkeypatch):
    import io
    import json

    calls = []

    def fake_urlopen(url, timeout):
        calls.append(url)
        return io.BytesIO(json.dumps({"rates": {"USD": 1, "NGN": 1600}}).encode())

    monkeypatch.setattr("bot.rates.urllib.request.urlopen", fake_urlopen)
    p = RateProvider(api_url="https://example.test/latest/USD")
    assert p.convert(2, "USD", "NGN") == 3200
    p.convert(1, "USD", "NGN")
    assert len(calls) == 1  # second call served from cache


def test_format_money():
    assert format_money(1234.5, "NGN") == "₦1,234.50 NGN"
    assert format_money(3, "KES") == "3.00 KES"


def test_faq_matching():
    assert "Naira" in best_answer("how do I pay you, bank transfer?", FAQ).answer
    assert "josephobaje264" in best_answer("what's your email", FAQ).answer
    assert best_answer("tell me a joke about cats", FAQ) is None
