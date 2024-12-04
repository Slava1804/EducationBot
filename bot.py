from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_TOKEN_BOT')

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Обработчик команды /start с использованием фильтра Command
@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.reply("Hello! I'm your bot.", parse_mode="HTML")

# Запуск бота
async def main():
    # Для aiogram 3.x используется executor для запуска
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())