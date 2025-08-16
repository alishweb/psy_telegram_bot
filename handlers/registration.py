from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from html import escape
import aiosqlite
import datetime
import re

# چون از این موارد در فایل questions.py هم استفاده می‌شود، اینجا تعریف می‌کنیم
from db import get_or_create_user, update_user_details
from middlewares import check_subscription, get_join_channels_keyboard
from config import MESSAGE_LIMIT, LIMIT_REACHED_MESSAGE

# تعریف State ها در یک مکان مرکزی
class Consultation(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone_number = State()
    waiting_for_city = State() # جایگزین grade شد
    waiting_for_question = State()

router = Router()

def get_ask_new_question_keyboard():
    buttons = [[InlineKeyboardButton(text="❓ پرسیدن سوال مشاوره جدید  ", callback_data="ask_new_question")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext, db: aiosqlite.Connection):
    if not await check_subscription(message.bot, message.from_user.id):
        await message.answer("⚠️ برای استفاده از ربات، ابتدا باید در کانال‌های زیر عضو شوید:", reply_markup=get_join_channels_keyboard())
        return

    user_data = await get_or_create_user(db, message.from_user.id)
    if user_data[0]:  # اگر کاربر قبلاً ثبت‌نام کرده
        current_month = datetime.datetime.now().month
        is_new_month = user_data[4] != current_month
        effective_count = 0 if is_new_month else user_data[3]
        
        if effective_count >= MESSAGE_LIMIT:
            await message.answer(LIMIT_REACHED_MESSAGE)
            return
        
        await message.answer(f"سلام {escape(user_data[0])} عزیز، خوش برگشتید! 👋", reply_markup=get_ask_new_question_keyboard())
    else: # اگر کاربر جدید است
        await message.answer("سلام! به ربات مشاوره خوش آمدید. 👋\n\nلطفاً نام و نام خانوادگی خود را ارسال کنید:")
        await state.set_state(Consultation.waiting_for_full_name)

@router.callback_query(F.data == "check_join")
async def check_join_callback(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    await callback.answer("در حال بررسی عضویت شما...", show_alert=False)
    if await check_subscription(callback.bot, callback.from_user.id):
        await callback.message.delete()
        user_data = await get_or_create_user(db, callback.from_user.id)
        if user_data[0]:
            await callback.message.answer(f"سلام {escape(user_data[0])} عزیز! عضویت شما تایید شد.✅", reply_markup=get_ask_new_question_keyboard())
        else:
            await callback.message.answer("عالی! عضویت شما تایید شد. ✅\n\nلطفاً نام و نام خانوادگی خود را ارسال کنید:")
            await state.set_state(Consultation.waiting_for_full_name)
    else:
        await callback.answer("❌ شما هنوز در تمام کانال‌ها عضو نشده‌اید.", show_alert=True)
        await callback.message.answer("⚠️ **بررسی ناموفق بود!**\n\nهنوز عضو تمام کانال‌ها نشده‌اید. لطفاً مجدداً تلاش کنید.")

@router.message(Consultation.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    # اعتبارسنجی نام
    name_pattern = r"^[\u0600-\u06FF\sA-Za-z]{3,50}$"
    if re.match(name_pattern, message.text) and ' ' in message.text:
        await state.update_data(full_name=message.text)
        await message.answer("متشکرم. اکنون لطفاً شماره تماس خود را ارسال کنید:")
        await state.set_state(Consultation.waiting_for_phone_number)
    else:
        await message.answer("❌ لطفاً نام و نام خانوادگی خود را به درستی وارد کنید.")

@router.message(Consultation.waiting_for_phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    # اعتبارسنجی شماره تلفن
    phone_pattern = r"^09\d{9}$"
    if re.match(phone_pattern, message.text):
        await state.update_data(phone_number=message.text)
        await message.answer("بسیار خب. حالا لطفاً شهر محل سکونت خود را وارد کنید:")
        await state.set_state(Consultation.waiting_for_city) # رفتن به حالت دریافت شهر
    else:
        await message.answer("❌ لطفاً شماره تلفن خود را به فرمت صحیح وارد کنید (مثلاً: 09123456789).")

@router.message(Consultation.waiting_for_city)
async def process_city(message: Message, state: FSMContext, db: aiosqlite.Connection):
    # می‌توانید برای شهر هم اعتبارسنجی اضافه کنید (مثلا طول متن)
    if len(message.text) > 2 and len(message.text) < 50:
        await state.update_data(city=message.text)
        data = await state.get_data()
        await update_user_details(db, message.from_user.id, data['full_name'], data['phone_number'], data['city'])
        await message.answer("اطلاعات شما با موفقیت ذخیره شد. ✅\nاکنون می‌توانید سوال خود را به طور کامل تایپ و ارسال کنید.")
        await state.set_state(Consultation.waiting_for_question)
    else:
        await message.answer("❌ لطفاً نام شهر را به درستی وارد کنید.")