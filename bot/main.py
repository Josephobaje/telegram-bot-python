"""Entry point: ``python -m bot``."""

from __future__ import annotations

import logging

from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from . import handlers
from .config import load_settings
from .faq import load_faq
from .rates import RateProvider

COMMANDS = [
    ("start", "Welcome message"),
    ("help", "Show what I can do"),
    ("remind", "Set a reminder"),
    ("reminders", "List pending reminders"),
    ("cancel", "Cancel your reminders"),
    ("rate", "Exchange rates vs Naira"),
    ("convert", "Convert currencies"),
    ("faq", "Frequently asked questions"),
]


def build_application(token: str, rates_api_url: str = "", faq_path=None) -> Application:
    from .config import Settings

    faq_file = faq_path or Settings(token=token).faq_path

    async def post_init(app: Application) -> None:
        await app.bot.set_my_commands([BotCommand(c, d) for c, d in COMMANDS])

    app = Application.builder().token(token).post_init(post_init).build()
    app.bot_data["rates"] = RateProvider(api_url=rates_api_url)
    app.bot_data["faq"] = load_faq(faq_file)

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help_command))
    app.add_handler(CommandHandler("remind", handlers.remind))
    app.add_handler(CommandHandler("reminders", handlers.list_reminders))
    app.add_handler(CommandHandler("cancel", handlers.cancel))
    app.add_handler(CommandHandler("rate", handlers.rate))
    app.add_handler(CommandHandler("convert", handlers.convert))
    app.add_handler(CommandHandler("faq", handlers.faq))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_message))
    app.add_error_handler(handlers.error_handler)
    return app


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = load_settings()
    app = build_application(settings.token, settings.rates_api_url, settings.faq_path)
    logging.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":  # pragma: no cover
    main()
