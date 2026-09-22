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

### Логирование API

Логирование настраивается через переменные окружения `AMNEZIA_API_*`:

| Переменная | Значение по умолчанию | Описание |
|------------|------------------------|----------|
| `AMNEZIA_API_LOG_LEVEL` | `INFO` | Уровень логирования (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `AMNEZIA_API_LOG_FILE` | *(пусто)* | Путь к вращающемуся файлу лога. Если пусто — пишутся только в stderr. |

При деплое через `api/deploy.sh` в systemd-юните задаётся
`AMNEZIA_API_LOG_FILE=/var/log/amnezia-vds-api.log` (ротация 10 МБ, 5 файлов).

Что логируется:

- **Запросы/ответы** — каждый запрос пишется через `amnezia.access` в формате
  `method=… path=… status=… duration_ms=… auth=… client=…`. Значение
  заголовка `X-API-Secret` не логируется, фиксируется только его наличие.
- **Команды управления** — запуск/успех/провал bash-скрипта (`amnezia.runner`).
  При неуспехе пишется **полный** (не обрезанный) stdout и stderr команды.
- **Операции с ключами и сервером** — генерация/скачивание/удаление/список
  ключей и check/restart сервера через `amnezia.api`.
- **Необработанные исключения** — стектрейс и 500-ответ (`amnezia.api`),
  чтобы ошибки не «молчали» в логах.

Примеры:

```bash
# почитать хвост лога API
sudo tail -f /var/log/amnezia-vds-api.log
```


## Telegram-бот

Файл секретов `/etc/amnezia-vds/bot.yml` создаётся автоматически с
заглушками при первом запуске. В нём нужно указать токен бота, адрес API,
секрет API и список разрешённых Telegram-никомов.

Команды бота: `/menu`, `/generate`, `/get`, `/delete`, `/list`,
`/restart`, `/help`, `/cancel`. Подробности в
`.claude/skills/python-dev/SKILL.md`.

Управление доступно и как команды, и через **inline-меню** (кнопка `/menu`):
Создать / Получить / Удалить ключ, Список ключей, Перезапустить. Список
ключей выводится красивой таблицей (библиотека `PrettyTable`).

### Деплой бота

```bash
sudo ./bot/deploy.sh
```

Скрипт ставит зависимости и регистрирует systemd-сервис `amnezia-vds-bot` с
автозапуском.

### Логирование бота

Логирование настраивается в файле `/etc/amnezia-vds/bot.yml` (секция
`logging`) или через переменные окружения `AMNEZIA_BOT_LOG_*`, которые
приоритетнее:

| Источник | Поле / переменная | По умолчанию | Описание |
|----------|-------------------|--------------|----------|
| yml | `logging.level` | `INFO` | Уровень логирования (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| env | `AMNEZIA_BOT_LOG_LEVEL` | — | То же, что выше (переопределяет). |
| yml | `logging.file` | *(пусто)* | Путь к вращающемуся файлу лога. |
| env | `AMNEZIA_BOT_LOG_FILE` | — | То же, что выше (переопределяет). |

При деплое через `bot/deploy.sh` в systemd-юните задаётся
`AMNEZIA_BOT_LOG_FILE=/var/log/amnezia-vds-bot.log` (ротация 10 МБ, 5 файлов).

Что логируется:

- **Обращения к API** — каждый вызов к HTTP API через `amnezia.bot.api`
  (генерация/скачивание/список/перезапуск) с именем ключа и размером файла.
  Секрет API не логируется.
- **Доступ пользователей** — каждый обработанный апдейт (`amnezia.bot.access`):
  `message`/`callback`, id и ник пользователя. Попытки доступа
  неавторизованных пользователей пишутся как `WARNING`.
- **Жизненный цикл** — запуск/остановка бота через `amnezia.bot`.

Loggers aiogram и httpx приглушены до `WARNING`, чтобы не засорять вывод.

Примеры:

```bash
# почитать хвост лога бота
sudo tail -f /var/log/amnezia-vds-bot.log
```
