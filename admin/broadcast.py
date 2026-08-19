import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

import config
import database as db


def register(app: Client):

    @app.on_message(filters.command("broadcast") & filters.private)
    async def broadcast_cmd(client: Client, message: Message):
        if message.from_user.id != config.ADMIN_ID:
            return

        text = message.text.split(maxsplit=1)
        if len(text) < 2:
            await message.reply(
                "Usage: `/broadcast <message>`\n"
                "پیام را برای همه کاربران فعال و غیربن‌شده می‌فرستد.",
                parse_mode="markdown",
            )
            return

        broadcast_text = text[1].strip()
        users = await db.list_users()
        active = [u for u in users if u["is_active"] and not u["is_banned"]]

        sent = 0
        failed = 0
        status = await message.reply(f"📢 در حال ارسال به {len(active)} کاربر...")

        for user in active:
            try:
                await client.send_message(user["telegram_id"], broadcast_text)
                sent += 1
                await asyncio.sleep(0.05)  # 20 msg/s — under Telegram flood limit
            except Exception:
                failed += 1

        await status.edit_text(
            f"📢 پیام همگانی کامل شد.\n✅ ارسال شد: {sent}\n❌ ناموفق: {failed}"
        )
