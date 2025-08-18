# psychology_bot/main.py
import asyncio
import logging
import aiosqlite

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from config import API_TOKEN
from middlewares import SubscriptionMiddleware
from handlers import registration, questions
from db import create_all_tables, ensure_consultants_in_db, DB_FILE

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    
    async with aiosqlite.connect(DB_FILE) as db:
        # ایجاد تمام جداول مورد نیاز برنامه
        await create_all_tables(db)
        # مطمئن می‌شویم که همه مشاوران در جدول آمار ثبت شده‌اند
        await ensure_consultants_in_db(db)

        dp = Dispatcher()

        dp.update.middleware(SubscriptionMiddleware())

        # ثبت روترها از فایل‌های handlers
        dp.include_router(registration.router)
        dp.include_router(questions.router)
        
        # تنظیم دستورات منو، شامل دستور جدید stats
        commands = [
            BotCommand(command="start", description="🚀 شروع مجدد و ثبت نام"),
            BotCommand(command="ask", description="❓ پرسیدن سوال جدید")
        ]
        await bot.set_my_commands(commands)
        
        print("🤖 Psychology Bot started...")
        # پاس دادن آبجکت db به تمام هندلرها
        await dp.start_polling(bot, db=db)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by admin.")