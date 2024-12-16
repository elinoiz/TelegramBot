import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import requests
import g4f

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
API_TOKEN = '7646001687:AAEQCEwB3eDHnZSxoeOJ7F40D2_4Rd-Kppg'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Настройка g4f
g4f.debug.logging = True  # Включение логирования
g4f.check_version = False  # Отключение автоматической проверки версии

# Конфигурация Mistral API
MISTRAL_API_URL = 'https://api.mistral.ai/v1/chat/completions'
MISTRAL_API_KEY = 'Rej7dFCCWSbzQtYs4CsSZsjByBn3uYwt'

# Функция для обработки команды /start
@dp.message(Command(commands=['start']))
async def send_welcome(message: Message):
    await message.reply("Привет! Укажите модель для запроса (Mistral или GPT) и отправьте ваш запрос.")

# Функция для обработки текстовых сообщений
@dp.message()
async def handle_message(message: Message):
    user_text = message.text

    # Анализ сообщения для определения модели
    if "Mistral" in user_text:
        model = "Mistral"
        query = user_text.replace("Mistral", "").strip()
    elif "GPT" in user_text:
        model = "GPT"
        query = user_text.replace("GPT", "").strip()
    else:
        await message.reply("Пожалуйста, укажите модель (Mistral или GPT) и отправьте ваш запрос.")
        return

    # Обработка запроса в зависимости от выбранной модели
    if model == "Mistral":
        response = make_mistral_request(query)
    elif model == "GPT":
        response = make_g4f_request(query)

    await message.reply(response)

# Функция для выполнения запроса к Mistral API
def make_mistral_request(query: str) -> str:
    headers = {
        'Authorization': f'Bearer {MISTRAL_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    }
    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
        response.raise_for_status()  # Вызовет исключение для HTTP ошибок
        logging.info(f"Response from Mistral API: {response.json()}")
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', 'Не удалось получить ответ.')
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        return f"HTTP ошибка: {http_err}"
    except Exception as err:
        logging.error(f"Other error occurred: {err}")
        return f"Ошибка: {err}"

# Функция для выполнения запроса к g4f
def make_g4f_request(query: str) -> str:
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": query}],
    )

    # Логирование ответа для отладки
    logging.info(f"Response from g4f: {response}")

    # Проверка типа ответа
    if isinstance(response, dict):
        reply_text = response.get('choices', [{}])[0].get('message', {}).get('content', 'Ошибка при получении ответа.')
    elif isinstance(response, str):
        reply_text = response
    else:
        reply_text = 'Ошибка при получении ответа.'

    return reply_text

# Функция для обработки ошибок
@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    logging.error(f'Update {update} caused error {exception}')

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
