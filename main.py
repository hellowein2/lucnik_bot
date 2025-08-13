import asyncio
from aiogram.types import Message
from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from os import getenv

TOKEN = getenv("TOKEN")
ADMIN_ID = getenv("ADMIN_ID")

dp = Dispatcher(bot=Bot(TOKEN))


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer('привет додик')



async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())



