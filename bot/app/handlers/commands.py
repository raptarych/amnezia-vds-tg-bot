"""Telegram bot command handlers.

Implements commands and a persistent inline "menu" keyboard. Flows that need a
key name (generate / get / delete) ask for it as plain text after the button is
pressed. All interactions are guarded by an allow-list based filter.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from prettytable import PrettyTable

from ..api import AmneziaClient, ApiError

router = Router()

HELP_TEXT = (
    "Управление Amnezia VPN\n\n"
    "/menu - открыть меню\n"
    "/generate - создать новый ключ\n"
    "/get - получить существующий ключ\n"
    "/delete - удалить ключ\n"
    "/list - список ключей и статистика\n"
    "/restart - перезапустить сервис\n"
    "/cancel - отменить текущее действие"
)

MENU_TEXT = "Выберите действие:"


class GenerateState(StatesGroup):
    """FSM states used to collect a key name for generation."""

    waiting_for_name = State()


class GetState(StatesGroup):
    """FSM states used to collect a key name for download."""

    waiting_for_name = State()


class DeleteState(StatesGroup):
    """FSM states used to collect a key name for deletion."""

    waiting_for_name = State()


def main_menu() -> InlineKeyboardMarkup:
    """Return the main inline keyboard with all actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗝 Создать ключ", callback_data="menu:generate"
                ),
                InlineKeyboardButton(text="📥 Получить ключ", callback_data="menu:get"),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить ключ", callback_data="menu:delete"
                ),
                InlineKeyboardButton(text="📋 Список ключей", callback_data="menu:list"),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Перезапустить", callback_data="menu:restart"
                )
            ],
        ]
    )


def _format_key_name(text: str) -> str:
    return text.strip()


# ---------------------------------------------------------------------------
# General commands / menu
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(HELP_TEXT)
    await message.answer(MENU_TEXT, reply_markup=main_menu())


@router.message(Command("menu"))
async def on_menu(message: Message) -> None:
    await message.answer(MENU_TEXT, reply_markup=main_menu())


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
# Inline menu actions
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "menu:generate")
async def menu_generate(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(GenerateState.waiting_for_name)
    await callback.message.answer("Введите имя нового ключа:")


@router.callback_query(F.data == "menu:get")
async def menu_get(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(GetState.waiting_for_name)
    await callback.message.answer("Введите имя ключа, который нужно скачать:")


@router.callback_query(F.data == "menu:delete")
async def menu_delete(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(DeleteState.waiting_for_name)
    await callback.message.answer("Введите имя ключа, который нужно удалить:")


@router.callback_query(F.data == "menu:list")
async def menu_list(callback: CallbackQuery, amnezia: AmneziaClient) -> None:
    await callback.answer()
    await send_list(callback.message, amnezia)


@router.callback_query(F.data == "menu:restart")
async def menu_restart(callback: CallbackQuery) -> None:
    await callback.answer()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, перезапустить", callback_data="confirm_restart"
                ),
                InlineKeyboardButton(
                    text="Отмена", callback_data="cancel_restart"
                ),
            ]
        ]
    )
    await callback.message.answer(
        "Точно перезапустить сервис?", reply_markup=keyboard
    )


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
# Delete a key
# ---------------------------------------------------------------------------

@router.message(Command("delete"))
async def delete_start(message: Message, state: FSMContext) -> None:
    await state.set_state(DeleteState.waiting_for_name)
    await message.answer("Введите имя ключа, который нужно удалить:")


@router.message(DeleteState.waiting_for_name, F.text)
async def delete_confirm(
    message: Message, state: FSMContext, amnezia: AmneziaClient
) -> None:
    name = _format_key_name(message.text or "")
    if not name:
        await message.answer("Имя не может быть пустым. Попробуйте ещё раз:")
        return

    stats = None
    try:
        stats = await amnezia.list_keys()
    except ApiError:
        pass

    exists = bool(stats and any(p.name == name for p in stats.peers))
    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, удалить", callback_data=f"confirm_delete:{name}"),
                InlineKeyboardButton(text="Отмена", callback_data="cancel_delete"),
            ]
        ]
    )
    hint = "" if exists else " (ключ с таким именем не найден в списке)"
    await message.answer(
        f"Точно удалить ключ `{name}`?{hint}", reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("confirm_delete:"))
async def do_delete(callback: CallbackQuery, amnezia: AmneziaClient) -> None:
    name = callback.data.split(":", 1)[1]
    await callback.answer()
    status_msg = await callback.message.answer(f"Удаляю ключ `{name}`...")
    try:
        await amnezia.delete_key(name)
    except ApiError as exc:
        await status_msg.edit_text(f"Ошибка при удалении ключа: {exc}")
        return
    await status_msg.edit_text(f"Ключ `{name}` удалён.")


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery) -> None:
    await callback.answer("Отменено.")
    await callback.message.answer("Удаление отменено.")


# ---------------------------------------------------------------------------
# List keys
# ---------------------------------------------------------------------------

@router.message(Command("list"))
async def list_keys_command(message: Message, amnezia: AmneziaClient) -> None:
    await send_list(message, amnezia)


def _render_stats_table(stats) -> str:
    """Render the key statistics as a bordered PrettyTable block."""
    table = PrettyTable()
    table.field_names = ["Имя", "IP", "Получено", "Отправлено", "Последний handshake", "Статус"]
    table.align["Имя"] = "l"
    table.align["IP"] = "l"
    for peer in stats.peers:
        table.add_row(
            [
                peer.name,
                peer.ip,
                peer.received,
                peer.sent,
                peer.last_handshake,
                peer.status,
            ]
        )
    table.max_width["Имя"] = 24
    table.max_width["Последний handshake"] = 24
    return table.get_string()


async def send_list(message: Message, amnezia: AmneziaClient) -> None:
    """Fetch stats and send a PrettyTable-formatted list to the user."""
    try:
        stats = await amnezia.list_keys()
    except ApiError as exc:
        await message.answer(f"Ошибка получения списка ключей: {exc}")
        return

    if not stats.peers:
        await message.answer("Ключи не найдены.", reply_markup=main_menu())
        return

    table = _render_stats_table(stats)
    totals = (
        f"Итого: Получено {stats.totals.received} · Отправлено {stats.totals.sent}"
    )
    await message.answer(
        f"<pre>{table}</pre>\n\n{totals}", parse_mode="HTML", reply_markup=main_menu()
    )


# ---------------------------------------------------------------------------
# Restart service
# ---------------------------------------------------------------------------

@router.message(Command("restart"))
async def restart_service(message: Message, amnezia: AmneziaClient) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, перезапустить", callback_data="confirm_restart"
                ),
                InlineKeyboardButton(text="Отмена", callback_data="cancel_restart"),
            ]
        ]
    )
    await message.answer("Точно перезапустить сервис?", reply_markup=keyboard)


@router.callback_query(F.data == "confirm_restart")
async def confirm_restart(
    callback: CallbackQuery, amnezia: AmneziaClient
) -> None:
    await callback.answer()
    status_msg = await callback.message.answer("Перезапускаю сервис...")
    try:
        await amnezia.restart_server()
    except ApiError as exc:
        await status_msg.edit_text(f"Ошибка перезапуска сервиса: {exc}")
        return
    await status_msg.edit_text("Сервис перезапущен.")


@router.callback_query(F.data == "cancel_restart")
async def cancel_restart(callback: CallbackQuery) -> None:
    await callback.answer("Отменено.")
    await callback.message.answer("Перезапуск отменён.")


# ---------------------------------------------------------------------------
# Unknown text / non-command input
# ---------------------------------------------------------------------------

@router.message(F.text, StateFilter(None))
async def unknown_message(message: Message) -> None:
    await message.answer("Неизвестная команда. Наберите /menu или /help.")
