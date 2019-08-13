# Telegram register bot

Bot to register and update user info.

## Getting Started

### Prerequisites

Python > v.3.7.4

### Installing

After clone.

Create virtual environment inside project folder.

```
python -m venv venv
```

Activate virtual env in Windows cmd.exe

```
venv\Scripts\activate.bat
```

Activate virtual env in Linux bash

```
venv/bin/activate
```

After activate virtual env, install dependecies with pip.

```
pip install -r requirements.txt
```

### Environment variables

| Name             | Descripton              |
| ---------------- | ----------------------- |
| MONGO_URL        | Mongo DB connection url |
| TELEGRAM_BOT_KEY | Telegram bot token      |

## Running it

```
python telebot.py
```

