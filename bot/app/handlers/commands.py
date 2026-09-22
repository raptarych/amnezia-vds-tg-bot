"""Telegram bot command handlers.

Implements a small set of textual commands backed by an FSM to collect a key
name where required. All interactions are guarded by an allow-list based
filter so that only configured Telegram usernames can use the bot.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from ..api import AmneziaClient, ApiError

router = Router()

HELP_TEXT = (
    "Управление Amnezia VPN\n\n"
    "/generate - создать новый ключ\n"
    "/get - получить существующий ключ\n"
    "/list - список ключей и статистика\n"
    "/restart - перезапустить сервис\n"
    "/cancel - отменить текущее действие"
)


class GenerateState(StatesGroup):
    """FSM states used to collect a key name for generation."""

    waiting_for_name = State()


class GetState(StatesGroup):
    """FSM states used to collect a key name for download."""

    waiting_for_name = State()


def _format_key_name(text: str) -> str:
    return text.strip()


# ---------------------------------------------------------------------------
# General commands
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("help"))
async def on_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("cancel"), StateFilter("*"))
async def on_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Нечего отменять.")
        return
    await state.clear()
    await message.answer("Действие отменено.")


# ---------------------------------------------------------------------------
# Generate a key
# ---------------------------------------------------------------------------

@router.message(Command("generate"))
async def generate_start(message: Message, state: FSMContext) -> None:
    await state.set_state(GenerateState.waiting_for_name)
    await message.answer("Введите имя нового ключа:")


@router.message(GenerateState.waiting_for_name, F.text)
async def generate_name(
    message: Message, state: FSMContext, amnezia: AmneziaClient
) -> None:
    name = _format_key_name(message.text or "")
    if not name:
        await message.answer("Имя не может быть пустым. Попробуйте ещё раз:")
        return
    await state.clear()
    status_msg = await message.answer(f"Создаю ключ `{name}`...")
    try:
        await amnezia.generate_key(name)
    except ApiError as exc:
        await status_msg.edit_text(f"Ошибка при создании ключа: {exc}")
        return
    await send_key_files(amnezia, message, name)


async def send_key_files(amnezia: AmneziaClient, message: Message, name: str) -> None:
    """Download and send the ``.conf`` and ``.png`` files to the user."""
    try:
        conf = await amnezia.download_key(name, "conf")
        png = await amnezia.download_key(name, "png")
    except ApiError as exc:
        await message.answer(f"Ключ создан, но не удалось скачать файлы: {exc}")
        return

    try:
        await message.answer_document(
            BufferedInputFile(conf, filename=f"{name}.conf"),
            caption=f"Конфигурация ключа `{name}`",
        )
        await message.answer_photo(
            BufferedInputFile(png, filename=f"{name}.png"),
            caption=f"QR-код ключа `{name}`",
        )
    except TelegramBadRequest as exc:
        if "PHOTO_INVALID_DIMENSIONS" in str(exc):
            await message.answer_document(
                BufferedInputFile(png, filename=f"{name}.png"),
                caption=f"QR-код ключа `{name}`",
            )
        else:
            await message.answer(f"Ошибка отправки файлов: {exc}")


# ---------------------------------------------------------------------------
# Get a key
# ---------------------------------------------------------------------------

@router.message(Command("get"))
async def get_start(message: Message, state: FSMContext) -> None:
    await state.set_state(GetState.waiting_for_name)
    await message.answer("Введите имя ключа, который нужно скачать:")


@router.message(GetState.waiting_for_name, F.text)
async def get_name(
    message: Message, state: FSMContext, amnezia: AmneziaClient
) -> None:
    name = _format_key_name(message.text or "")
    if not name:
        await message.answer("Имя не может быть пустым. Попробуйте ещё раз:")
        return
    await state.clear()
    await send_key_files(amnezia, message, name)


# ---------------------------------------------------------------------------
# List keys
# ---------------------------------------------------------------------------

@router.message(Command("list"))
async def list_keys(
    message: Message, amnezia: AmneziaClient
) -> None:
    try:
        stats = await amnezia.list_keys()
    except ApiError as exc:
        await message.answer(f"Ошибка получения списка ключей: {exc}")
        return

    if not stats.peers:
        await message.answer("Ключи не найдены.")
        return

    rows = [
        (
            "Имя          | IP              | Получено | Отправлено | "
            "Последний handshake | Статус"
        ),
        "---",
    ]
    for peer in stats.peers:
        rows.append(
            f"{peer.name} | {peer.ip} | {peer.received} | {peer.sent} | "
            f"{peer.last_handshake} | {peer.status}"
        )
    table = "\n".join(rows)
    await message.answer(f"<pre>{table}</pre>", parse_mode="HTML")


# ---------------------------------------------------------------------------
# Restart service
# ---------------------------------------------------------------------------

@router.message(Command("restart"))
async def restart_service(message: Message, amnezia: AmneziaClient) -> None:
    status_msg = await message.answer("Перезапускаю сервис...")
    try:
        await amnezia.restart_server()
    except ApiError as exc:
        await status_msg.edit_text(f"Ошибка перезапуска сервиса: {exc}")
        return
    await status_msg.edit_text("Сервис перезапущен.")


# ---------------------------------------------------------------------------
# Telegram callback: confirm restart
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "confirm_restart")
async def confirm_restart(
    callback: CallbackQuery, amnezia: AmneziaClient
) -> None:
    await callback.answer()
    await callback.message.answer("Перезапускаю сервис...")
    try:
        await amnezia.restart_server()
    except ApiError as exc:
        await callback.message.answer(f"Ошибка перезапуска сервиса: {exc}")
        return
    await callback.message.answer("Сервис перезапущен.")


# ---------------------------------------------------------------------------
# Unknown text / non-command input
# ---------------------------------------------------------------------------

@router.message(F.text, StateFilter(None))
async def unknown_message(message: Message) -> None:
    await message.answer("Неизвестная команда. Наберите /help.")
