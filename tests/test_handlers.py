"""Handler tests with lightweight fakes, so no network or real bot token is needed."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot import handlers
from bot.faq import load_faq
from bot.main import build_application
from bot.rates import RateProvider

FAQ = load_faq(Path(__file__).resolve().parents[1] / "bot" / "faq.json")


def make_update(text="", chat_id=42):
    message = SimpleNamespace(text=text, reply_text=AsyncMock())
    return SimpleNamespace(
        message=message,
        effective_chat=SimpleNamespace(id=chat_id),
        effective_user=SimpleNamespace(first_name="Ada"),
    )


def make_context(args=None, jobs=None):
    job_queue = MagicMock()
    job_queue.get_jobs_by_name.return_value = jobs or []
    return SimpleNamespace(args=args or [], job_queue=job_queue, bot_data={"rates": RateProvider(), "faq": FAQ})


def reply(update) -> str:
    return update.message.reply_text.await_args.args[0]


async def test_start_greets_user():
    u = make_update()
    await handlers.start(u, make_context())
    assert "Hi Ada" in reply(u)


async def test_remind_schedules_job():
    u, c = make_update(), make_context(["10m", "Call", "mum"])
    await handlers.remind(u, c)
    c.job_queue.run_once.assert_called_once()
    _, kwargs = c.job_queue.run_once.call_args
    assert c.job_queue.run_once.call_args.args[1] == 600
    assert kwargs["chat_id"] == 42 and kwargs["data"] == "Call mum"
    assert "10 minutes" in reply(u)


async def test_remind_invalid():
    u, c = make_update(), make_context(["soon", "x"])
    await handlers.remind(u, c)
    c.job_queue.run_once.assert_not_called()
    assert reply(u).startswith("⚠️")


async def test_cancel_removes_jobs():
    jobs = [MagicMock(), MagicMock()]
    u = make_update()
    await handlers.cancel(u, make_context(jobs=jobs))
    assert all(j.schedule_removal.called for j in jobs)
    assert "Cancelled 2" in reply(u)


async def test_convert_command():
    u = make_update()
    await handlers.convert(u, make_context(["100", "USD", "NGN"]))
    assert reply(u) == "$100.00 USD = ₦155,000.00 NGN"


async def test_rate_command_labels_sample_rates():
    u = make_update()
    await handlers.rate(u, make_context())
    assert "Sample rates" in reply(u) and "1 USD = ₦1,550.00 NGN" in reply(u)


async def test_free_text_uses_faq():
    u = make_update("How much does an app cost?")
    await handlers.text_message(u, make_context())
    assert "quote" in reply(u)


async def test_free_text_fallback():
    u = make_update("blue elephants")
    await handlers.text_message(u, make_context())
    assert "/faq" in reply(u)


def test_build_application_registers_handlers():
    app = build_application("123456:TEST-TOKEN")
    assert len(app.handlers[0]) == 9
    assert app.job_queue is not None


def test_missing_token(monkeypatch, tmp_path):
    from bot.config import load_settings

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        load_settings()
