import os
import base64
import logging
import asyncio
from aiohttp import web
import aiohttp_cors
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile

# --- НАСТРОЙКИ ---
# Токен мы добавим в настройках сайта Render, чтобы не светить его тут
TOKEN = os.getenv("BOT_TOKEN") 
# Ссылка на Vercel (появится позже)
VERCEL_URL = os.getenv("VERCEL_URL", "google.com")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 1. ЧТО БОТ ПИШЕТ В ТЕЛЕГРАМЕ ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Нарисовать открытку 🎨", 
            web_app=WebAppInfo(url=f"https://{VERCEL_URL}") 
        )]
    ])
    await message.answer(
        "Привет! Это проект «Джингл белс дизайнеры».\n"
        "Нажми кнопку, нарисуй шедевр, и я пришлю его тебе файлом.", 
        reply_markup=markup
    )

# --- 2. СЕРВЕР ДЛЯ ПРИЕМА КАРТИНОК ---
async def handle_upload(request):
    try:
        data = await request.json()
        image_data = data.get('image').split(',')[1] # Убираем заголовок base64
        user_id = data.get('user_id')
        
        # Превращаем текст картинки обратно в байты
        img_bytes = base64.b64decode(image_data)
        # Готовим файл для отправки
        input_file = BufferedInputFile(img_bytes, filename="new_year_card.jpg")

        # Отправляем пользователю в чат
        await bot.send_photo(
            chat_id=user_id,
            photo=input_file,
            caption="Готово! С Новым Годом! 🎄"
        )
        return web.Response(text="OK")
    except Exception as e:
        logging.error(f"Error: {e}")
        return web.Response(text=str(e), status=500)

async def health_check(request):
    return web.Response(text="Bot is alive!")

# --- 3. ЗАПУСК ВСЕГО ВМЕСТЕ ---
async def main():
    app = web.Application()
    app.router.add_post('/upload_image', handle_upload)
    app.router.add_get('/', health_check)

    # Разрешаем сайту (Vercel) отправлять нам данные (CORS)
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["POST", "OPTIONS"]
        )
    })
    for route in list(app.router.routes()):
        cors.add(route)

    runner = web.AppRunner(app)
    await runner.setup()
    # Render сам скажет, какой порт использовать
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port=port)
    await site.start()
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
