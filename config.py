import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN_PSYCHOLOGY")
OWNER_ID = int(os.getenv("OWNER_ID"))

CONSULTANT_IDS_STR = os.getenv("CONSULTANT_IDS_PSYCHOLOGY", "")
if not CONSULTANT_IDS_STR:
    raise ValueError("حداقل یک آیدی مشاور در فایل .env در متغیر CONSULTANT_IDS_PSYCHOLOGY نیاز است.")

CONSULTANT_IDS = [int(cid.strip()) for cid in CONSULTANT_IDS_STR.split(',')]


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