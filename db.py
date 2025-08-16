import aiosqlite

DB_FILE = "psychology_bot.db"

async def create_tables(db: aiosqlite.Connection):
    await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            phone_number TEXT,
            city TEXT,
            message_count INTEGER DEFAULT 0,
            last_message_month INTEGER DEFAULT 0
        )
    ''')
    await db.commit()

async def get_or_create_user(db: aiosqlite.Connection, user_id: int):
    async with db.execute("SELECT full_name, phone_number, city, message_count, last_message_month FROM users WHERE user_id = ?", (user_id,)) as cursor:
        user_data = await cursor.fetchone()
    if user_data is None:
        await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()
        return (None, None, None, 0, 0)
    return user_data

async def update_user_details(db: aiosqlite.Connection, user_id: int, full_name: str, phone_number: str, city: str):
    await db.execute("UPDATE users SET full_name=?, phone_number=?, city=? WHERE user_id=?", (full_name, phone_number, city, user_id))
    await db.commit()


async def increment_message_count(db: aiosqlite.Connection, user_id: int, current_month: int):
    await db.execute("UPDATE users SET message_count = message_count + 1, last_message_month = ? WHERE user_id = ?", (current_month, user_id))
    await db.commit()

async def reset_monthly_limit(db: aiosqlite.Connection, user_id: int, current_month: int):
    await db.execute("UPDATE users SET message_count = 1, last_message_month = ? WHERE user_id = ?", (current_month, user_id))
    await db.commit()