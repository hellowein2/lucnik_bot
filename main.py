import asyncio

from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import Dispatcher, Bot, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import CommandStart
from aiogram.fsm.state import StatesGroup, State
from os import getenv
from sqlalchemy import Column, Integer, select, String, delete
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

class Link(Base):
    __tablename__ = "links"
    link = Column(String, primary_key=True)

class Link_state(StatesGroup):
    Link_waiting = State()

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

async def get_all_users_id(session: AsyncSession):
    result = await session.execute(select(User.chat_id))
    return [row[0] for row in result.all()]

async def get_link(session: AsyncSession):
    result = await session.execute(select(Link.link))
    return [row[0] for row in result.all()]



@dp.message(CommandStart())
async def start(message: Message):
    async with AsyncSessionLocal() as session:
        admin = await session.get(Admin, message.chat.id)
        if admin:
            button = [
                [KeyboardButton(text='Я покурил нахуй!')],
                [KeyboardButton(text='Анонс стрима')],
            ]
            kb = ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True, one_time_keyboard=False)
            await message.answer('Привет, ты админ', reply_markup=kb)
            return
        user = await session.get(User, message.chat.id)
        if not user:
            new_user = User(chat_id=message.chat.id)
            session.add(new_user)
            await session.commit()
        await message.answer('Привет, теперь ты будешь получать рассылку о начале стримов и конце перекуров!')

@dp.message(F.text == 'Анонс стрима')
async def link_broadcast(message: Message, state: FSMContext):
    async with AsyncSessionLocal() as session:
        admin = await session.get(Admin, message.chat.id)
        if admin:
            await message.answer('Пришли время и ссылку')
            await state.set_state(Link_state.Link_waiting
                                  )
@dp.message(F.text == 'Я покурил нахуй!')
async def broadcast(message: Message, state=FSMContext):
    async with AsyncSessionLocal() as session:
        admin = await session.get(Admin, message.chat.id)
        if admin:
            if await state.get_state() == Link_state.Link_waiting:
                await state.clear()
            link = await get_link(session)
            users_id = await get_all_users_id(session)
            if link:
                for user_id in users_id:
                    try:
                        await bot.send_message(text=f'Жора покурил!\n{link[0]}', chat_id=user_id)
                        await asyncio.sleep(0.05)
                    except (TelegramForbiddenError, TelegramNotFound):
                        await session.execute(delete(User).where(User.chat_id == user_id))
            else:
                for user_id in users_id:
                    try:
                        await bot.send_message(text=f'Жора покурил!', chat_id=user_id)
                        await asyncio.sleep(0.05)
                    except (TelegramForbiddenError, TelegramNotFound):
                        await session.execute(delete(User).where(User.chat_id == user_id))
            await message.answer(text='Отправил!')


@dp.message(F.text, Link_state.Link_waiting)
async def save_link(message: Message, state: FSMContext):
    async with AsyncSessionLocal() as session:
        new_link = Link(link=message.text)
        users_id = await get_all_users_id(session)
        for user_id in users_id:
            try:
                await bot.send_message(text=message.text, chat_id=user_id)
                await asyncio.sleep(0.05)
            except (TelegramForbiddenError, TelegramNotFound):
                await session.execute(delete(User).where(User.chat_id == user_id))
        await session.execute(delete(Link))
        session.add(new_link)
        await session.commit()
    await message.answer(text='Отправил!')
    await state.clear()


async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())



