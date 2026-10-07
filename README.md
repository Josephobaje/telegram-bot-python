# Telegram Assistant Bot (Python)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-v21%2B-26A5E4?logo=telegram&logoColor=white)
![Tests](https://img.shields.io/badge/tests-35%20passing-brightgreen)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

A Telegram bot for small businesses and freelancers, built with [python-telegram-bot](https://python-telegram-bot.org/) (async, v21+). It sets **reminders**, shows **exchange rates against the Naira**, converts currencies, and answers **frequently asked questions** in plain English.

## Features

| Command | What it does |
| --- | --- |
| `/start`, `/help` | Welcome message and command list |
| `/remind 10m Call the client` | One-off reminder. Accepts `30s`, `10m`, `1h30m`, `2d` (up to 30 days) |
| `/reminders` | Lists your pending reminders |
| `/cancel` | Cancels all your reminders |
| `/rate` | USD, GBP, EUR, CAD and GHS against the Naira |
| `/convert 100 USD NGN` | Converts between currencies (also `/convert 50000 naira to dollar`) |
| `/faq` | Shows all FAQ entries |
| `/contact` | Shows your contact details (name, email, optional phone, website), set through `CONTACT_*` env vars |
| any text | Matches the message against the FAQ by keywords and replies with the best answer |

Also included:

- The token is read from the `TELEGRAM_BOT_TOKEN` environment variable or a `.env` file. Nothing secret lives in the code.
- The rate provider can be swapped: it uses clearly labelled sample rates by default, or live rates from any JSON API through `RATES_API_URL`, cached for 10 minutes.
- Reminders run on the built-in `JobQueue` (APScheduler), with a limit of 20 per chat.
- FAQ answers live in `bot/faq.json`, so they can be edited without touching code.
- The bot command menu is registered automatically on startup.
- 35 tests cover the parsing logic and the handlers, using fakes, so no token or network is needed.

## Tech stack

Python 3.10+, python-telegram-bot 21+ (asyncio), APScheduler (JobQueue), pytest, pytest-asyncio

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy its token.
2. Install and configure:

```bash
git clone https://github.com/Josephobaje/telegram-bot-python.git
cd telegram-bot-python
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env    # then paste your token into .env
```

3. Run it:

```bash
python -m bot
```

Open your bot in Telegram and send `/start`.

### Live exchange rates

Set `RATES_API_URL` in `.env` to an endpoint that returns `{"rates": {"USD": 1, "NGN": ...}}`, for example `https://open.er-api.com/v6/latest/USD`. Without it, `/rate` uses sample rates and says so.

### Contact details

`/contact` replies with a plain-text contact card. Configure it in `.env` (unset or empty values use the defaults):

| Variable | Default |
| --- | --- |
| `CONTACT_NAME` | `Joseph Obaje` |
| `CONTACT_EMAIL` | `josephobaje264@gmail.com` |
| `CONTACT_PHONE` | none (the phone line is hidden) |
| `CONTACT_URL` | `https://github.com/Josephobaje` |

### Deploying

The bot uses long polling, so it runs anywhere Python runs: a VPS with `systemd` or `pm2`, Railway, Render (background worker), or PythonAnywhere. Set `TELEGRAM_BOT_TOKEN` as an environment variable on the host.

## Running tests

```bash
pytest
```

## Project structure

```text
bot/
  main.py        # builds the Application and registers handlers
  handlers.py    # async command and message handlers
  reminders.py   # duration parsing ("1h30m") and reminder validation
  rates.py       # rate provider (sample or live API) and conversion
  faq.py         # keyword FAQ matcher
  faq.json       # editable FAQ content
  config.py      # environment / .env settings
tests/           # pytest suite (logic + handlers with fakes)
```

## Author

**Joseph Obaje**, Full Stack Developer (PHP, Python, Flutter) and Cybersecurity Specialist

- GitHub: [@Josephobaje](https://github.com/Josephobaje)
- LinkedIn: [joseph-obaje](https://www.linkedin.com/in/joseph-obaje)
- Email: [josephobaje264@gmail.com](mailto:josephobaje264@gmail.com)

## License

Released under the [MIT License](LICENSE). © 2026 Joseph Obaje
