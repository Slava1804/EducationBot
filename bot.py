import os
import asyncio
import requests
import re
import aiohttp
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Message, PreCheckoutQuery, LabeledPrice, CallbackQuery, BotCommandScopeChat

load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_TOKEN_BOT')
DJANGO_API_URL = os.getenv('DJANGO_API_URL', 'http://127.0.0.1:8000/api/users/')
STATS_API_URL = os.getenv('STATS_API_URL', 'http://127.0.0.1:8000/api/users/stats/')
PAYMENT_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
class WordCountStates(StatesGroup):
    waiting_for_text = State()

# Асинхронная функция для работы с API
async def get_user_data(telegram_id: int):
    response = requests.get(f"{DJANGO_API_URL}{telegram_id}/")
    if response.status_code == 200:
        return response.json()
    return None

async def is_user_registered(telegram_id: int) -> bool:
    """
    Проверяет, зарегистрирован ли пользователь по Telegram ID.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{DJANGO_API_URL}{telegram_id}/") as response:
            if response.status == 200:
                # Пользователь существует в базе данных
                return True
            elif response.status == 404:
                # Пользователь не найден
                return False
            else:
                # Произошла ошибка
                raise Exception(f"Ошибка при проверке пользователя: {response.status}")

async def update_user_tasks(telegram_id: int, tasks_completed: int, daily_tasks_completed: int):
    async with aiohttp.ClientSession() as session:
        async with session.patch(
            f"{DJANGO_API_URL}{telegram_id}/update_tasks/",
            json={
                "tasks_completed": tasks_completed,
                "daily_tasks_completed": daily_tasks_completed,
            }
        ) as response:
            return response.status == 200

async def check_subscriptions():
    """
    Проверяет окончание подписки у пользователей и отправляет уведомления.
    """
    async with aiohttp.ClientSession() as session:
        try:
            # Получаем всех пользователей
            async with session.get(DJANGO_API_URL) as response:
                if response.status == 200:
                    users = await response.json()

                    for user in users:
                        telegram_id = user.get("telegram_id")
                        subscription_end = user.get("subscription_end")  # Дата окончания подписки
                        is_subscribed = user.get("is_subscribed", False)

                        if subscription_end and is_subscribed:
                            # Преобразуем строку даты в объект datetime
                            subscription_end_date = datetime.strptime(subscription_end, "%Y-%m-%d")
                            days_left = (subscription_end_date - datetime.now()).days

                            if days_left == 2:  # Если осталось 2 дня
                                await bot.send_message(
                                    chat_id=telegram_id,
                                    text=(
                                        "📢 Уважаемый пользователь!\n\n"
                                        "Ваша подписка заканчивается через 2 дня. "
                                        "Продлите её, чтобы продолжить пользоваться ботом без ограничений."
                                    )
                                )
                            elif days_left < 0:  # Если подписка истекла
                                update_data = {"is_subscribed": False}
                                async with session.patch(f"{DJANGO_API_URL}{telegram_id}/", json=update_data) as update_response:
                                    if update_response.status == 200:
                                        print(f"Подписка пользователя {telegram_id} деактивирована.")
                else:
                    print(f"Ошибка получения пользователей: {response.status}")
        except Exception as e:
            print(f"Ошибка проверки подписок: {e}")

async def fetch_statistics():
    try:
        response = requests.get(STATS_API_URL)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.RequestException as e:
        print(f"Ошибка при запросе статистики: {e}")
        return None

@dp.startup()
async def on_startup(bot: Bot):
    async with aiohttp.ClientSession() as session:
        try:
            # Получаем всех пользователей
            async with session.get(DJANGO_API_URL) as response:
                if response.status == 200:
                    users = await response.json()
                    # Обходим всех пользователей и настраиваем команды
                    for user in users:
                        telegram_id = user.get("telegram_id")
                        is_registered = await is_user_registered(telegram_id)
                        if telegram_id and is_registered:
                            try:
                                await set_bot_commands(bot, telegram_id)
                            except Exception as e:
                                print(f"Ошибка при установке команд для пользователя {telegram_id}: {e}")
                else:
                    print(f"Ошибка получения списка пользователей: {response.status}")
        except Exception as e:
            print(f"Ошибка при запросе к API: {e}")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_subscriptions, "interval", days=1)  # Запускать ежедневно
    scheduler.start()
    print("Фоновая проверка подписок запущена.")

async def set_bot_commands(bot: Bot, telegram_id: int):
    commands = [
        BotCommand(command="/word_count", description="Подсчет слов"),
        BotCommand(command="/subscribe", description="Оплата подписки"),
    ]

    try:
        is_registered = await is_user_registered(telegram_id)
        if is_registered:
            # Проверяем, является ли пользователь администратором
            user = await get_user_data(telegram_id)
            if user and user.get('is_admin', False):  # Проверяем, что пользователь является администратором
                commands.extend([
                    BotCommand(command="/admin_stats", description="Статистика (только для администраторов)"),
                    BotCommand(command="/add_admin", description="Добавить админа (только для администраторов)"),
                ])
    except Exception as e:
        print(f"Ошибка при получении данных пользователя {telegram_id}: {e}")
    
    try:
        # Устанавливаем команды для пользователя
        await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=telegram_id))
    except Exception as e:
        print(f"Ошибка при установке команд для чата {telegram_id}: {e}")

# Создание инлайн-меню
def get_inline_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Регистрация", callback_data="register")],
    ])
    return keyboard
class AddAdminStates(StatesGroup):
    waiting_for_telegram_id = State()

# Команда /add_admin
@dp.message(Command("add_admin"))
async def add_admin_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    # Проверка является ли пользователь администратором
    user_data = await get_user_data(telegram_id)
    if not user_data or not user_data.get("is_admin", False):
        await message.reply("У вас нет прав для выполнения этой команды.")
        return

    # Запрос у администратора ID нового администратора
    await message.reply("Введите Telegram ID пользователя, которого вы хотите сделать администратором.")
    await state.set_state(AddAdminStates.waiting_for_telegram_id)

# Обработчик для ввода нового admin
@dp.message(AddAdminStates.waiting_for_telegram_id)
async def process_add_admin(message: Message, state: FSMContext):
    try:
        new_admin_id = int(message.text)  # Преобразование введенный текст в число

        # Проверка существует ли пользователь с таким Telegram ID
        user_data = await get_user_data(new_admin_id)
        if not user_data:
            await message.reply(f"Пользователь с Telegram ID {new_admin_id} не найден.")
            await state.clear()
            return

        # Обновляем данные пользователя через API
        async with aiohttp.ClientSession() as session:
            update_data = {"is_admin": True}
            async with session.patch(f"{DJANGO_API_URL}{new_admin_id}/", json=update_data) as response:
                if response.status == 200:
                    await message.reply(f"Пользователь с Telegram ID {new_admin_id} теперь является администратором.")
                else:
                    await message.reply("Ошибка при обновлении данных пользователя. Попробуйте позже.")
        
        await state.clear()  # Очищение состояния

    except ValueError:
        # Если ввод не является числом
        await message.reply("Пожалуйста, введите корректный Telegram ID.")
    except Exception as e:
        # Обработка прочих ошибок
        await message.reply(f"Произошла ошибка: {e}")
        await state.clear()

@dp.message(Command('start'))
async def start_command(message: Message):
    await message.reply(
        "Добро пожаловать! Зарегистрируйтесь для работы с ботом.",
        reply_markup=get_inline_menu()  # Показываем кнопку для регистрации
    )

@dp.callback_query(lambda callback: callback.data == "register")
async def process_register_callback(callback: CallbackQuery):
    # Вызываем обработчик `register_user` с использованием данных callback.message
    message = callback.message
    telegram_id = message.chat.id
    username = message.chat.username or "Unknown"
    
    data = {
        "telegram_id": telegram_id,
        "username": username,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(DJANGO_API_URL, json=data) as response:
            if response.status == 201:
                await message.reply(f"Регистрация прошла успешно, {username}.")
            elif response.status == 400:
                await message.reply("Вы уже зарегистрированы.")
            else:
                await message.reply("Произошла ошибка, пожалуйста, повторите позже.")

    # Уведомляем пользователя, что обработка завершена
    await callback.answer()  # Закрывает уведомление о нажатии

@dp.message(Command('word_count'))
async def word_count_command(message: Message, state: FSMContext):
    # Этот обработчик срабатывает при вводе команды /word_count
    await message.reply("Пожалуйста, отправьте текст для подсчета слов.")
    await state.set_state(WordCountStates.waiting_for_text)  # Переход к состоянию ожидания текста

@dp.callback_query()
async def handle_callbacks(callback: CallbackQuery, state: FSMContext):
    if callback.data == "word_count":
        await callback.message.reply("Пожалуйста, отправьте текст для подсчета слов.")
        await state.set_state(WordCountStates.waiting_for_text)  # Ставим состояние на ожидание текста
        await callback.answer()

@dp.message(WordCountStates.waiting_for_text)
async def count_words(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    try:
        user_data = await get_user_data(telegram_id)  # Получение данных пользователя
        if not user_data:
            await message.reply("Зарегистрируйтесь для работы с ботом.")
            await state.clear()
            return

        # Проверяем подписку и лимит
        is_subscribed = user_data.get('is_subscribed', False)
        tasks_completed = user_data.get('tasks_completed', 0)

        if not is_subscribed and tasks_completed >= 5:
            await message.reply("Вы превысили лимит задач за день. Оформите подписку для продолжения.")
            await state.clear()
            return

        # Подсчет слов
        text = message.text
        words = re.sub(r'[^\w\s]', '', text).split()
        word_count = {word: words.count(word) for word in words}

        sorted_words = sorted(word_count.items())
        output = "<b>📊 Частота слов:</b>\n\n"
        for word, count in sorted_words:
            output += f"<b>{word}</b>: <i>{count}</i> раз(а)\n"

        await message.reply(output, parse_mode="HTML")

        # Обновляем статистику
        await update_user_tasks(
            telegram_id=telegram_id,
            tasks_completed=1,
            daily_tasks_completed=1,
        )

        await state.clear()

    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")
        await state.clear()

# Команда для оформления подписки
@dp.message(Command("subscribe"))
async def subscribe(message: Message):
    telegram_id = message.from_user.id

    try:
        # Проверяем, зарегистрирован ли пользователь
        user_data = await get_user_data(telegram_id)  # Функция для получения данных пользователя

        if not user_data:
            await message.reply(
                "Для оформления подписки вы должны зарегистрироваться.",
                reply_markup=get_inline_menu()  # Показываем кнопку для регистрации
            )
            return

        # Проверяем наличие активной подписки
        if user_data.get("is_subscribed"):
            await message.reply("У вас уже есть активная подписка. Спасибо, что пользуетесь нашим ботом!")
            return

    except Exception as e:
        await message.reply(f"Произошла ошибка при проверке регистрации: {e}")
        return

    # Продолжение оформления подписки
    price = 29000  # Цена в копейках (29000 = 290 рублей)

    # Определим список цен для инвойса (можно добавить разные тарифы)
    prices = [LabeledPrice(label="Подписка на месяц", amount=price)]

    # Генерируем уникальный payload для отслеживания оплаты
    payload = f"subscription-{telegram_id}-{price}"

    # Отправка инвойса
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Оформление подписки на бот",
        description="Оплата за подписку на 1 месяц.",
        provider_token=PAYMENT_TOKEN,
        currency="rub",
        prices=prices,
        payload=payload,
        start_parameter="subscription",
        is_flexible=False
    )

# Обработка предоплаты
@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Ответ на запрос предоплаты, чтобы подтвердить платеж
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Обработка успешной оплаты
@dp.message(lambda message: message.successful_payment is not None)
async def handle_successful_payment(message: Message):
    # Данные успешной оплаты
    payment_info = message.successful_payment
    amount = payment_info.total_amount / 100  # Сумма в рублях
    currency = payment_info.currency
    user_id = message.from_user.id

    # Проверка и обновление подписки в базе данных
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{DJANGO_API_URL}{user_id}/") as response:
            if response.status == 200:
                user_data = await response.json()
                is_subscribed = user_data.get("is_subscribed", False)
                current_subscription_end = user_data.get("subscription_end")

                # Вычисляем новую дату окончания подписки
                today = datetime.now()
                if current_subscription_end:
                    # Если подписка уже была, продлеваем от текущей даты окончания
                    current_end_date = datetime.strptime(current_subscription_end, "%Y-%m-%dT%H:%M:%S")
                    new_subscription_end = max(current_end_date, today) + timedelta(days=30)
                else:
                    # Если подписки не было, начинаем отсчет с текущей даты
                    new_subscription_end = today + timedelta(days=30)

                # Обновляем данные подписки
                update_data = {
                    "is_subscribed": True,
                    "subscription_end": new_subscription_end.isoformat()
                }

                async with session.patch(f"{DJANGO_API_URL}{user_id}/", json=update_data) as update_response:
                    if update_response.status == 200:
                        await message.reply(
                            f"🎉 Спасибо за оплату!\n"
                            f"💰 Сумма: {amount} {currency}\n"
                            f"Подписка активирована до {new_subscription_end.strftime('%Y-%m-%d')}!"
                        )
                    else:
                        await message.reply("Ошибка активации подписки. Попробуйте позже.")
            else:
                await message.reply("Ошибка получения данных пользователя. Попробуйте позже.")

async def is_admin(telegram_id: int) -> bool:
    """Функция для проверки, является ли пользователь администратором."""
    user_data = await get_user_data(telegram_id)
    return user_data.get("is_admin", False)

@dp.message(Command("admin_stats"))
async def admin_stats(message: Message):
    user_id = message.from_user.id
    if await is_admin(user_id):
        try:
            response = requests.get(f"{DJANGO_API_URL}{user_id}/daily_statistics/")
            # Логируем ответ
            print(response.text)  # Логируем текст ответа

            # Проверяем, что ответ корректен
            if response.status_code == 200:
                stats = response.json()
                if isinstance(stats, dict):
                    stats_message = "<b>📊 Ежедневная статистика:</b>\n\n"
                    for user_id, user in stats.items():
                        username, daily_tasks, tasks = user.values()
                        stats_message += f"<b>{username} – {user_id}</b>\n  Количество за день: <b>{daily_tasks}</b>\n  Общее количество: <b>{tasks}\n\n</b>"
                    await message.reply(stats_message, parse_mode="HTML")
                else:
                    await message.reply("Не удалось получить статистику. Ответ не в формате JSON.", parse_mode="HTML")
            else:
                await message.reply(f"Ошибка при получении статистики: {response.status_code}", parse_mode="HTML")
        except requests.exceptions.RequestException as e:
            await message.reply(f"Ошибка при обращении к серверу: {e}", parse_mode="HTML")
    else:
        await message.reply("У вас нет прав администратора.", parse_mode="HTML")

async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())  # Запуск бота