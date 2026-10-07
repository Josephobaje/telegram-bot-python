"""Telegram command and message handlers."""

from __future__ import annotations

import logging

from telegram import LinkPreviewOptions, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from .config import ContactInfo
from .faq import best_answer
from .rates import RateError, format_money, parse_convert_args
from .reminders import ReminderError, humanize, parse_reminder

log = logging.getLogger(__name__)

HELP_TEXT = (
    "<b>Here's what I can do</b>\n\n"
    "/remind &lt;time&gt; &lt;message&gt; - set a reminder (e.g. <code>/remind 10m Call mum</code>)\n"
    "/reminders - list your pending reminders\n"
    "/cancel - cancel all your reminders\n"
    "/rate - exchange rates against the Naira\n"
    "/convert &lt;amount&gt; &lt;from&gt; &lt;to&gt; - e.g. <code>/convert 100 USD NGN</code>\n"
    "/faq - frequently asked questions\n"
    "/contact - how to reach me\n\n"
    "Or just ask me a question in plain English."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = update.effective_user.first_name if update.effective_user else "there"
    await update.message.reply_text(f"Hi {name}! 👋\n\n{HELP_TEXT}", parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def _send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.send_message(job.chat_id, f"⏰ Reminder: {job.data}")


def _job_name(chat_id: int) -> str:
    return f"reminder-{chat_id}"


async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    try:
        reminder = parse_reminder(context.args or [])
    except ReminderError as exc:
        await update.message.reply_text(f"⚠️ {exc}")
        return
    pending = context.job_queue.get_jobs_by_name(_job_name(chat_id))
    if len(pending) >= 20:
        await update.message.reply_text("⚠️ You already have 20 pending reminders. Use /cancel to clear them.")
        return
    context.job_queue.run_once(
        _send_reminder, reminder.seconds, chat_id=chat_id, name=_job_name(chat_id), data=reminder.text
    )
    await update.message.reply_text(f"✅ Okay! I'll remind you in {humanize(reminder.seconds)}: {reminder.text}")


async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    jobs = context.job_queue.get_jobs_by_name(_job_name(update.effective_chat.id))
    if not jobs:
        await update.message.reply_text("You have no pending reminders.")
        return
    lines = [f"• {job.data} (at {job.next_t:%H:%M} UTC)" for job in jobs]
    await update.message.reply_text("Your reminders:\n" + "\n".join(lines))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    jobs = context.job_queue.get_jobs_by_name(_job_name(update.effective_chat.id))
    for job in jobs:
        job.schedule_removal()
    await update.message.reply_text(f"🗑️ Cancelled {len(jobs)} reminder(s).")


async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    provider = context.bot_data["rates"]
    try:
        lines = [f"1 {c} = {format_money(provider.convert(1, c, 'NGN'), 'NGN')}" for c in ("USD", "GBP", "EUR", "CAD", "GHS")]
    except Exception:  # network or provider error
        log.exception("Rate lookup failed")
        await update.message.reply_text("⚠️ Couldn't fetch rates right now. Please try again later.")
        return
    note = "Live rates" if provider.is_live else "Sample rates (configure RATES_API_URL for live data)"
    await update.message.reply_text("💱 " + note + "\n\n" + "\n".join(lines))


async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    provider = context.bot_data["rates"]
    try:
        amount, src, dst = parse_convert_args(context.args or [])
        result = provider.convert(amount, src, dst)
    except RateError as exc:
        await update.message.reply_text(f"⚠️ {exc}")
        return
    await update.message.reply_text(f"{format_money(amount, src)} = {format_money(result, dst)}")


async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entries = context.bot_data["faq"]
    text = "\n\n".join(f"<b>{e.question}</b>\n{e.answer}" for e in entries)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


def format_contact(contact: ContactInfo) -> str:
    """Plain-text contact card. Lines with empty values are left out."""
    lines = [f"📇 Contact {contact.name}", ""]
    if contact.email:
        lines.append(f"📧 Email: {contact.email}")
    if contact.phone:
        lines.append(f"📞 Phone: {contact.phone}")
    if contact.url:
        lines.append(f"🌐 Website: {contact.url}")
    return "\n".join(lines)


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    info = context.bot_data.get("contact") or ContactInfo()
    # Sent as plain text (no parse_mode), so values from env vars can't inject markup.
    await update.message.reply_text(format_contact(info), link_preview_options=LinkPreviewOptions(is_disabled=True))


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entry = best_answer(update.message.text or "", context.bot_data["faq"])
    if entry:
        await update.message.reply_text(entry.answer)
    else:
        await update.message.reply_text("I'm not sure about that yet. Try /faq or /help.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Unhandled error", exc_info=context.error)
