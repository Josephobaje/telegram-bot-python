"""Settings loaded from environment variables (never hard-code the bot token)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv(path: Path = Path(".env")) -> None:
    """Minimal .env loader so the bot runs without extra dependencies."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


DEFAULT_CONTACT_NAME = "Joseph Obaje"
DEFAULT_CONTACT_EMAIL = "josephobaje264@gmail.com"
DEFAULT_CONTACT_URL = "https://github.com/Josephobaje"


@dataclass(frozen=True)
class ContactInfo:
    """Details shown by /contact. Phone is optional and has no default."""

    name: str = DEFAULT_CONTACT_NAME
    email: str = DEFAULT_CONTACT_EMAIL
    phone: str = ""
    url: str = DEFAULT_CONTACT_URL


def load_contact() -> ContactInfo:
    """Read CONTACT_NAME, CONTACT_EMAIL, CONTACT_PHONE and CONTACT_URL; unset or empty values use the defaults."""

    def env(key: str, default: str) -> str:
        return os.environ.get(key, "").strip() or default

    return ContactInfo(
        name=env("CONTACT_NAME", DEFAULT_CONTACT_NAME),
        email=env("CONTACT_EMAIL", DEFAULT_CONTACT_EMAIL),
        phone=env("CONTACT_PHONE", ""),
        url=env("CONTACT_URL", DEFAULT_CONTACT_URL),
    )


@dataclass(frozen=True)
class Settings:
    token: str
    rates_api_url: str = ""
    faq_path: Path = Path(__file__).with_name("faq.json")
    contact: ContactInfo = field(default_factory=ContactInfo)


def load_settings() -> Settings:
    _load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env and add your token from @BotFather.")
    return Settings(token=token, rates_api_url=os.environ.get("RATES_API_URL", "").strip(), contact=load_contact())
