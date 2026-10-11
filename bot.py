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
from aiogram.types import Message

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


@dp.message(Command("random"))
async def cmd_random(message: Message) -> None:
    playlist = load_playlist()
    song = random.choice(playlist)
    name = song["name"]
    artist = song["artist"] or '-'
    minutes, seconds = divmod(int(song["duration"]), 60)
    mes = f"🎵 {name}\n👤 {artist}\n⏱ {minutes:02d}:{seconds:02d}"
    await message.answer(mes)


@dp.message(Command("count"))
async def cmd_count(message: Message) -> None:
    playlist = load_playlist()
    await message.answer(f"В плейлисте {len(playlist)} песен.")


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!")


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
