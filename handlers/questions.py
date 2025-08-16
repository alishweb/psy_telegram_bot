from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from html import escape
import datetime
import aiosqlite
import re
import logging

from .registration import Consultation, get_ask_new_question_keyboard
from db import get_or_create_user, increment_message_count, reset_monthly_limit
from config import CONSULTANT_ID, MESSAGE_LIMIT, LIMIT_REACHED_MESSAGE

router = Router()

async def pre_question_check(db: aiosqlite.Connection, user_id: int):
    """Auxiliary function to check the user's status and quota before each question."""
    user_data = await get_or_create_user(db, user_id)
    
    if not user_data[0]:  # If the full name is not available
        return "not_registered", None
    
    current_month = datetime.datetime.now().month
    message_count = user_data[3]
    last_message_month = user_data[4]
    
    is_new_month = last_message_month != current_month
    effective_count = 0 if is_new_month else message_count
    
    if effective_count >= MESSAGE_LIMIT:
        return "limit_reached", None
    
    return "ok", user_data

@router.message(Command("ask", "soal"))
async def command_ask_handler(message: Message, state: FSMContext, db: aiosqlite.Connection):
    status, _ = await pre_question_check(db, message.from_user.id)
    
    if status == "not_registered":
        await message.answer("شما هنوز ثبت‌نام نکرده‌اید. لطفاً ابتدا از دستور /start استفاده کنید.")
    elif status == "limit_reached":
        await message.answer(LIMIT_REACHED_MESSAGE)
    else:  # status == "ok"
        await message.answer("لطفاً سوال خود را تایپ و ارسال کنید:")
        await state.set_state(Consultation.waiting_for_question)

@router.callback_query(F.data == "ask_new_question")
async def ask_new_question_callback(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    await callback.answer()
    status, _ = await pre_question_check(db, callback.from_user.id)
    
    if status == "limit_reached":
        await callback.message.answer(LIMIT_REACHED_MESSAGE)
    else:  # status == "ok" or "not_registered"
        await callback.message.answer("لطفاً سوال خود را ارسال کنید:")
        await state.set_state(Consultation.waiting_for_question)

@router.message(Consultation.waiting_for_question)
async def process_question(message: Message, state: FSMContext, db: aiosqlite.Connection):
    user_id = message.from_user.id
    try:
        current_month = datetime.datetime.now().month
        status, user_data = await pre_question_check(db, user_id)
        
        if status == "limit_reached":
            await message.answer(LIMIT_REACHED_MESSAGE, reply_markup=get_ask_new_question_keyboard())
            return

        full_name, phone_number, city, message_count, last_message_month = user_data
        is_new_month = last_message_month != current_month
        
        final_message = (
            f"📩 <b>درخواست مشاوره جدید (روانشناسی)</b>\n\n"
            f"<b>نام:</b> {escape(full_name)}\n"
            f"<b>تماس:</b> {escape(phone_number)}\n"
            f"<b>شهر:</b> {escape(city)}\n"
            f"<b>آیدی کاربر:</b> <code>{user_id}</code>\n"
            f"<b>یوزرنیم:</b> @{message.from_user.username or 'ندارد'}\n\n"
            f"<b>سوال:</b>\n{escape(message.text)}"
        )
        
        await message.bot.send_message(CONSULTANT_ID, final_message)
        await message.answer("✅ سوال شما با موفقیت برای مشاور ارسال شد.")
        
        if is_new_month:
            await reset_monthly_limit(db, user_id, current_month)
            new_count = 1
        else:
            await increment_message_count(db, user_id, current_month)
            new_count = message_count + 1

        remaining = MESSAGE_LIMIT - new_count
        if remaining > 0:
            await message.answer(f"شما می‌توانید {remaining} سوال دیگر در این ماه بپرسید.", reply_markup=get_ask_new_question_keyboard())
        else:
            await message.answer(LIMIT_REACHED_MESSAGE, reply_markup=get_ask_new_question_keyboard())
            
    except Exception as e:
        logging.error(f"Error in process_question: {e}")
        await message.answer("❌ متاسفانه در ارسال پیام به مشاور خطایی رخ داد.")
    finally:
        await state.clear()


@router.message(F.from_user.id == CONSULTANT_ID, F.reply_to_message)
async def handle_consultant_reply(message: Message):
    match = re.search(r"آیدی کاربر: (\d+)", message.reply_to_message.text)
    if not match:
        await message.reply("⚠️ خطا: نتوانستم آیدی کاربر را در این پیام پیدا کنم.")
        return
        
    user_id = int(match.group(1))
    try:
        await message.bot.send_message(user_id, f"✉️ پاسخ از طرف مشاور:\n\n---\n{message.text}", reply_markup=get_ask_new_question_keyboard())
        await message.reply("✅ پاسخ شما با موفقیت برای کاربر ارسال شد.")
    except Exception as e:
        logging.error(f"Failed to send reply to {user_id}: {e}")
        await message.reply(f"❌ خطا در ارسال پیام به کاربر (ID: {user_id}). احتمالاً ربات بلاک شده است.")