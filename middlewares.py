import logging
from aiogram import BaseMiddleware, types, Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import CHANNELS

def get_join_channels_keyboard():
    buttons = [
        [InlineKeyboardButton(text=f"📢 عضویت در کانال {i+1}", url=f"https://t.me/{c.lstrip('@')}")]
        for i, c in enumerate(CHANNELS)
    ]
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_join")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def check_subscription(bot: Bot, user_id: int) -> bool:
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logging.error(f"Error checking subscription for {channel}: {e}")
            return False
    return True

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Update, data):
        user = data.get('event_from_user')
        if not user:
            return await handler(event, data)
            
        state = data.get('state')
        # --- بخش اصلاح شده ---
        # اگر کاربر در هر یک از حالت‌های FSM بود، میدل‌ور کاری به او ندارد
        # این کار از تداخل در فرآیند ثبت‌نام و پرسش سوال جلوگیری می‌کند
        if await state.get_state() is not None:
            return await handler(event, data)
        # --- پایان بخش اصلاح شده ---

        # استثناها: برای این موارد هم میدل‌ور اجرا نشود
        if event.message and event.message.text and event.message.text.startswith("/start"):
            return await handler(event, data)
        if event.callback_query and event.callback_query.data == "check_join":
            return await handler(event, data)

        bot = data['bot']
        if not await check_subscription(bot, user.id):
            await bot.send_message(
                user.id,
                "⚠️ برای ادامه فعالیت در ربات، باید در کانال‌های زیر عضو باشید:",
                reply_markup=get_join_channels_keyboard()
            )
            return
        
        return await handler(event, data)