from dotenv import load_dotenv
import pymorphy3
import asyncio
import logging
import json, random
from pathlib import Path
import sys, os
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile)
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Any, Awaitable, Callable, Dict


class AccessMiddleware(BaseMiddleware):
    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user and user.id != self.admin_id:
            return
        return await handler(event, data)

morph = pymorphy3.MorphAnalyzer()
noun = morph.parse('песня')[0]
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
if not TOKEN:
    raise ValueError("Не найден BOT_TOKEN. Проверь файл .env")

PLAYLIST_PATH = Path(__file__).parent / "playlist.json"

dp = Dispatcher()
dp.message.middleware(AccessMiddleware(admin_id=ADMIN_ID))
dp.callback_query.middleware(AccessMiddleware(admin_id=ADMIN_ID))

def load_playlist():
    with open(PLAYLIST_PATH, "r", encoding="utf-8") as f:
        playlist = json.load(f)
    return playlist

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Случайная песня", callback_data="random"), 
             InlineKeyboardButton(text="📊 Счёт", callback_data="count")], 
            [InlineKeyboardButton(text="🔍 Найти трек", callback_data="find"),
             InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
        ],
        
    )
    return keyboard

def build_song_text(song):
    name = song["name"]
    artist = song["artist"] or '-'
    minutes, seconds = divmod(int(song["duration"]), 60)
    mes = f"🎵 {name}\n👤 {artist}\n⏱ {minutes:02d}:{seconds:02d}"
    return mes


def pick_random_song():
    playlist = load_playlist()
    index = random.randrange(len(playlist))
    return playlist[index], index


def get_audio_keyboard(index):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="⬇️ Отправить файл",
                                 callback_data=f"send_audio:{index}")
        ]]
    )
    return keyboard


def build_count_text():
    playlist = load_playlist()
    word = noun.make_agree_with_number(len(playlist)).word
    return f"В плейлисте {len(playlist)} {word}."


def build_find_text(query):
    if len(query) > 1:
        query = query[-1].lower()
        playlist = load_playlist()
        result = [build_song_text(song) for song in playlist if query in song["name"].lower() or query in (song["artist"] or "").lower()]
        if result:
            word = noun.make_agree_with_number(len(result)).word
            return f"Нашёл: {len(result)} {word}:" + "\n\n" + "\n\n".join(result)
        return f'Ничего не найдено по запросу "{query}".'
    return "Напиши, что искать. Пример: /find club"


def build_start_text(message):
    return f"""Привет, {html.bold(message)}! 👋

Я — бот-помощник для твоего плейлиста.

Что я умею:
🎲 /random — случайная песня
📊 /count — сколько песен в плейлисте
🔍 /find {html.quote('<текст>')} — поиск по названию или артисту
❓ /help — эта справка

Или нажми на кнопку ниже 👇"""



@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(build_start_text(message.from_user.full_name), reply_markup=get_main_keyboard())


@dp.callback_query()
async def on_callback(callback: CallbackQuery) -> None:
    if callback.data == "random":
        await callback.answer()  # просто подтверждение, без текста
        song, idx = pick_random_song()
        # сообщение в чат
        await callback.message.answer(build_song_text(song), reply_markup=get_audio_keyboard(idx))
    elif "send_audio" in callback.data:
        await callback.answer()
        playlist = load_playlist()
        idx = int(callback.data.split(":")[1])
        song = playlist[int(idx)]
        audio = FSInputFile(song["path"])
        await callback.message.answer_audio(
            audio,
            title=song["name"],
            performer=song["artist"] or "-",
        )
    elif callback.data == "count":
        await callback.answer()  # просто подтверждение, без текста
        await callback.message.answer(build_count_text())  # сообщение в чат
    elif callback.data == "find":
        await callback.answer()  # просто подтверждение, без текста
        await callback.message.answer("Напиши команду /find и запрос. Пример: /find club")  # сообщение в чат
    elif callback.data == "help":
        await callback.answer()  # просто подтверждение, без текста
        await callback.message.answer(build_start_text(callback.from_user.full_name), reply_markup=get_main_keyboard())


@dp.message(Command("random"))
async def cmd_random(message: Message) -> None:
    song, idx = pick_random_song()
    await message.answer(build_song_text(song), reply_markup=get_audio_keyboard(idx))


#@dp.message(Command("send"))
#async def cmd_send(message: Message) -> None:
#    await message.answer_audio("C:\\Users\\legion\\Music\\audio.mp3")


@dp.message(Command("count"))
async def cmd_count(message: Message) -> None:
    await message.answer(build_count_text())


@dp.message(Command("find"))
async def cmd_find(message: Message) -> None:
    await message.answer(build_find_text(message.text.split(maxsplit=1)))


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(build_start_text(message.from_user.full_name), reply_markup=get_main_keyboard())


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
