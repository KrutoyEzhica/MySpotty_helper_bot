from dotenv import load_dotenv
import asyncio
import logging
import json, random
from pathlib import Path
import sys, os
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton)


load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не найден BOT_TOKEN. Проверь файл .env")

PLAYLIST_PATH = Path(__file__).parent / "playlist.json"

dp = Dispatcher()


def load_playlist():
    with open(PLAYLIST_PATH, "r", encoding="utf-8") as f:
        playlist = json.load(f)
    return playlist

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Случайная песня", callback_data="random"), 
             InlineKeyboardButton(text="📊 Счёт", callback_data="count")]
        ]
    )
    return keyboard

def build_random_song_text():
    playlist = load_playlist()
    song = random.choice(playlist)
    name = song["name"]
    artist = song["artist"] or '-'
    minutes, seconds = divmod(int(song["duration"]), 60)
    mes = f"🎵 {name}\n👤 {artist}\n⏱ {minutes:02d}:{seconds:02d}"
    return mes


def build_count_text():
    playlist = load_playlist()
    return f"В плейлисте {len(playlist)} песен."


@dp.callback_query()
async def on_callback(callback: CallbackQuery) -> None:
    if callback.data == "random":
        await callback.answer()  # просто подтверждение, без текста
        await callback.message.answer(build_random_song_text())  # сообщение в чат
    elif callback.data == "count":
        await callback.answer()  # просто подтверждение, без текста
        await callback.message.answer(build_count_text())  # сообщение в чат


@dp.message(Command("random"))
async def cmd_random(message: Message) -> None:
    await message.answer(build_random_song_text())


@dp.message(Command("count"))
async def cmd_count(message: Message) -> None:
    await message.answer(build_count_text())


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!", reply_markup=get_main_keyboard())


@dp.message()
async def echo_handler(message: Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
