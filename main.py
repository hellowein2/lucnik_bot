import asyncio
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from os import getenv
from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

TOKEN = getenv("TOKEN")
ADMIN_ID = getenv("ADMIN_ID")

Base = declarative_base()
dp = Dispatcher(bot=Bot(TOKEN))
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


class User(Base):
    __tablename__ = "users"
    chat_id = Column(Integer, primary_key=True)

class Admin(Base):
    __tablename__ = "admins"
    chat_id = Column(Integer, primary_key=True)


engine = create_async_engine('sqlite+aiosqlite:///ignore/database.db', echo=False)
AsyncSessionLocal: sessionmaker[AsyncSession] = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        admin = await session.get(Admin, ADMIN_ID)
        if not admin:
            new_admin = Admin(chat_id=ADMIN_ID)
            session.add(new_admin)
            await session.commit()



@dp.message(CommandStart())
async def start(message: Message):
    async with AsyncSessionLocal() as session:
        admin = await session.get(Admin, message.chat.id)
        if admin:
            button = InlineKeyboardButton(text='Я покурил нахуй!', callback_data='start_broadcast')
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [button]
            ])
            await message.reply('Привет, ты админ', reply_markup=keyboard)
            return
        user = await session.get(User, message.chat.id)
        if not user:
            new_user = User(chat_id=message.chat.id)
            session.add(new_user)
            await session.commit()
        await message.answer('привет додик')



async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())



