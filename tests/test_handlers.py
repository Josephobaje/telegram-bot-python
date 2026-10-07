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
    assert len(app.handlers[0]) == 10
    assert app.job_queue is not None


def test_missing_token(monkeypatch, tmp_path):
    from bot.config import load_settings

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        load_settings()


def test_contact_card_defaults():
    from bot.config import ContactInfo

    text = handlers.format_contact(ContactInfo())
    assert "Joseph Obaje" in text
    assert "josephobaje264@gmail.com" in text
    assert "https://github.com/Josephobaje" in text
    assert "Phone" not in text  # no default phone number


async def test_contact_command_replies_with_configured_details():
    from bot.config import ContactInfo

    u, c = make_update(), make_context()
    c.bot_data["contact"] = ContactInfo(name="Ada Lovelace", email="ada@example.com", phone="+234 800 000 0000", url="https://example.com")
    await handlers.contact(u, c)
    text = reply(u)
    assert "Contact Ada Lovelace" in text
    assert "ada@example.com" in text and "+234 800 000 0000" in text and "https://example.com" in text
    kwargs = u.message.reply_text.await_args.kwargs
    assert "parse_mode" not in kwargs  # plain text, so env values can't inject markup
    assert kwargs["link_preview_options"].is_disabled


async def test_contact_command_falls_back_to_defaults():
    u, c = make_update(), make_context()  # no "contact" in bot_data
    await handlers.contact(u, c)
    assert "josephobaje264@gmail.com" in reply(u)


def test_load_contact_from_env(monkeypatch):
    from bot.config import load_contact

    for key in ("CONTACT_NAME", "CONTACT_EMAIL", "CONTACT_PHONE", "CONTACT_URL"):
        monkeypatch.delenv(key, raising=False)
    assert load_contact().phone == ""
    assert load_contact().email == "josephobaje264@gmail.com"

    monkeypatch.setenv("CONTACT_NAME", "JO Digital")
    monkeypatch.setenv("CONTACT_EMAIL", "  hello@example.com ")
    monkeypatch.setenv("CONTACT_PHONE", "+234 801 234 5678")
    monkeypatch.setenv("CONTACT_URL", "")  # empty falls back to the default
    info = load_contact()
    assert info.name == "JO Digital"
    assert info.email == "hello@example.com"
    assert info.phone == "+234 801 234 5678"
    assert info.url == "https://github.com/Josephobaje"


def test_load_settings_includes_contact(monkeypatch, tmp_path):
    from bot.config import load_settings

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:TEST-TOKEN")
    monkeypatch.setenv("CONTACT_PHONE", "+234 802 000 0000")
    assert load_settings().contact.phone == "+234 802 000 0000"


def test_contact_listed_in_help_and_command_menu():
    from bot.main import COMMANDS

    assert "/contact" in handlers.HELP_TEXT
    assert "contact" in dict(COMMANDS)


def test_build_application_stores_contact(monkeypatch):
    from bot.config import ContactInfo

    monkeypatch.delenv("CONTACT_EMAIL", raising=False)
    assert build_application("123456:TEST-TOKEN").bot_data["contact"].email == "josephobaje264@gmail.com"
    custom = ContactInfo(name="Ada")
    assert build_application("123456:TEST-TOKEN", contact=custom).bot_data["contact"] is custom
