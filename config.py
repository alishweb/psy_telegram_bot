import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN_PSYCHOLOGY")
CONSULTANT_ID_STR = os.getenv("CONSULTANT_ID_PSYCHOLOGY")

CONSULTANT_ID = int(CONSULTANT_ID_STR)

CHANNELS = ['@aiimpact_ir', '@ai_agent_farsi']
MESSAGE_LIMIT = 2

LIMIT_REACHED_MESSAGE = (
    "⚠️ شما به حداکثر پیام های مشاوره روانشناسی خود در این ماه رسیده اید\n\n"
    "برای دریافت مشاوره بیشتر، لطفاً با شماره‌های زیر تماس بگیرید:\n"
    "📞 <b>021-88785701</b>\n"
    "📱 <b>0999-1044844</b>\n"
    "لینک درخواست مشاوره از سایت: \n"
    "https://toofanpsy.ir/contact"
)