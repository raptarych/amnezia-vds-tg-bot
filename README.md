# amnezia-vds-tg-bot

Управление Amnezia VPN на Ubuntu 24 через пару приложений:

1. **`api/`** — HTTP API для управления Amnezia VPN на хосте (FastAPI).
2. **`bot/`** — Telegram-бот с poll-механикой (aiogram), который ходит в это API.

## Структура

```
api/            HTTP API (FastAPI)
  app/          исходный код приложения
  openapi.json  сгенерированная OpenAPI-спецификация (в git)
  tests/        тесты
  deploy.sh     деплой на Ubuntu 24 (systemd)
bot/            Telegram-бот (aiogram)
  app/          код бота
  client/       клиент, сгенерированный из openapi.json
  tests/        тесты
  config.example.yml  шаблон файла секретов
  deploy.sh     деплой на Ubuntu 24 (systemd)
.claude/skills/python-dev/SKILL.md  документация команд
```

## HTTP API

Все запросы требуют заголовок `X-API-Secret` (эталон хранится в
`/etc/amnezia-vds/api_secret`). Эндпоинты и параметры описаны в
`.claude/skills/python-dev/SKILL.md` и в самой OpenAPI-спецификации.

Локальный запуск для разработки:

```bash
cd api
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Тесты: `pytest tests -q`. Спецификацию можно перегенерировать командой
`python gen_openapi.py`.

### Деплой API

```bash
sudo AMNEZIA_API_SECRET=... ./api/deploy.sh
```

Скрипт ставит зависимости, создаёт systemd-сервис `amnezia-vds-api`,
регистрирует автозапуск и проверяет доступность API снаружи.

## Telegram-бот

Файл секретов `/etc/amnezia-vds/bot.yml` создаётся автоматически с
заглушками при первом запуске. В нём нужно указать токен бота, адрес API,
секрет API и список разрешённых Telegram-никомов.

Команды бота: `/generate`, `/get`, `/list`, `/restart`, `/help`, `/cancel`.
Подробности в `.claude/skills/python-dev/SKILL.md`.

### Деплой бота

```bash
sudo ./bot/deploy.sh
```

Скрипт ставит зависимости и регистрирует systemd-сервис `amnezia-vds-bot` с
автозапуском.
