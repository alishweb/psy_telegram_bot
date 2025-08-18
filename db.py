# psychology_bot/db.py
import aiosqlite
from config import CONSULTANT_IDS

# نام فایل دیتابیس مخصوص این ربات
DB_FILE = "psychology_bot.db"

async def create_all_tables(db: aiosqlite.Connection):
    """تمام جداول مورد نیاز برنامه را با ساختار جدید ایجاد می‌کند."""
    # جدول کاربران با ستون city و assigned_consultant_id
    await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            phone_number TEXT,
            city TEXT,
            message_count INTEGER DEFAULT 0,
            last_message_month INTEGER DEFAULT 0,
            assigned_consultant_id INTEGER
        )
    ''')
    # جدول آمار مشاوران با ستون‌های نام و یوزرنیم
    await db.execute('''
        CREATE TABLE IF NOT EXISTS consultant_stats (
            consultant_id INTEGER PRIMARY KEY,
            consultant_name TEXT,
            consultant_username TEXT,
            assigned_questions INTEGER DEFAULT 0,
            answered_questions INTEGER DEFAULT 0
        )
    ''')
    # جدول تنظیمات برای نوبت‌دهی
    await db.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    ''')
    await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('next_consultant_index', 0)")
    await db.commit()

async def ensure_consultants_in_db(db: aiosqlite.Connection):
    """مطمئن می‌شود که تمام مشاوران در جدول آمار وجود دارند."""
    for cid in CONSULTANT_IDS:
        await db.execute("INSERT OR IGNORE INTO consultant_stats (consultant_id) VALUES (?)", (cid,))
    await db.commit()

async def get_or_create_user(db: aiosqlite.Connection, user_id: int):
    """اطلاعات کاربر را با ستون city می‌خواند."""
    query = "SELECT full_name, phone_number, city, message_count, last_message_month, assigned_consultant_id FROM users WHERE user_id = ?"
    async with db.execute(query, (user_id,)) as cursor:
        user_data = await cursor.fetchone()
    if user_data is None:
        await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()
        return (None, None, None, 0, 0, None)
    return user_data

async def update_user_details(db: aiosqlite.Connection, user_id: int, full_name: str, phone_number: str, city: str):
    """اطلاعات کاربر را با ستون city آپدیت می‌کند."""
    await db.execute("UPDATE users SET full_name=?, phone_number=?, city=? WHERE user_id=?", (full_name, phone_number, city, user_id))
    await db.commit()

async def assign_consultant_to_user(db: aiosqlite.Connection, user_id: int, consultant_id: int):
    """یک مشاور را برای همیشه به یک کاربر اختصاص می‌دهد."""
    await db.execute("UPDATE users SET assigned_consultant_id = ? WHERE user_id = ?", (consultant_id, user_id))
    await db.commit()

async def update_consultant_info(db: aiosqlite.Connection, consultant_id: int, name: str, username: str):
    """نام و یوزرنیم مشاور را در جدول آمار ذخیره یا آپدیت می‌کند."""
    await db.execute(
        "UPDATE consultant_stats SET consultant_name = ?, consultant_username = ? WHERE consultant_id = ?",
        (name, username, consultant_id)
    )
    await db.commit()

async def increment_message_count(db: aiosqlite.Connection, user_id: int, current_month: int):
    await db.execute("UPDATE users SET message_count = message_count + 1, last_message_month = ? WHERE user_id = ?", (current_month, user_id))
    await db.commit()

async def reset_monthly_limit(db: aiosqlite.Connection, user_id: int, current_month: int):
    await db.execute("UPDATE users SET message_count = 1, last_message_month = ? WHERE user_id = ?", (current_month, user_id))
    await db.commit()

async def get_next_consultant_index(db: aiosqlite.Connection) -> int:
    async with db.execute("SELECT value FROM settings WHERE key = 'next_consultant_index'") as cursor:
        row = await cursor.fetchone()
        return row[0] if row else 0

async def update_next_consultant_index(db: aiosqlite.Connection, new_index: int):
    await db.execute("UPDATE settings SET value = ? WHERE key = 'next_consultant_index'", (new_index,))
    await db.commit()

async def increment_assigned_count(db: aiosqlite.Connection, consultant_id: int):
    await db.execute("UPDATE consultant_stats SET assigned_questions = assigned_questions + 1 WHERE consultant_id = ?", (consultant_id,))
    await db.commit()

async def increment_answered_count(db: aiosqlite.Connection, consultant_id: int):
    await db.execute("UPDATE consultant_stats SET answered_questions = answered_questions + 1 WHERE consultant_id = ?", (consultant_id,))
    await db.commit()

async def get_all_stats(db: aiosqlite.Connection):
    query = "SELECT consultant_id, consultant_name, consultant_username, assigned_questions, answered_questions FROM consultant_stats"
    async with db.execute(query) as cursor:
        return await cursor.fetchall()