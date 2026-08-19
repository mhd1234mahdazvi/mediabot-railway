from pyrogram import Client, filters
from pyrogram.types import Message

import config
import database as db


def register(app: Client):

    @app.on_message(filters.command("adduser") & filters.private)
    async def add_user_cmd(client: Client, message: Message):
        if message.from_user.id != config.ADMIN_ID:
            return

        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("Usage: `/adduser <@username or user_id>`", parse_mode="markdown")
            return

        target = parts[1].strip()
        try:
            if target.startswith("@"):
                user = await client.get_users(target)
            else:
                user = await client.get_users(int(target))

            await db.add_user(
                telegram_id=user.id,
                username=user.username or "",
                display_name=user.first_name or str(user.id),
                added_by=message.from_user.id,
            )
            await message.reply(
                f"✅ اضافه شد: **{user.first_name}** (`{user.id}`)\n"
                f"نام کاربری: @{user.username or 'N/A'}",
                parse_mode="markdown",
            )
        except Exception as e:
            await message.reply(f"❌ ناموفق: `{e}`", parse_mode="markdown")

    @app.on_message(filters.command("removeuser") & filters.private)
    async def remove_user_cmd(client: Client, message: Message):
        if message.from_user.id != config.ADMIN_ID:
            return

        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("Usage: `/removeuser <user_id>`", parse_mode="markdown")
            return

        try:
            user_id = int(parts[1].strip())
            await db.remove_user(user_id)

            # notify the user
            try:
                await client.send_message(user_id, "❌ دسترسی شما به این ربات حذف شد.")
            except Exception:
                pass

            await message.reply(f"✅ کاربر `{user_id}` حذف شد.", parse_mode="markdown")
        except ValueError:
            await message.reply("❌ Invalid user ID.")

    @app.on_message(filters.command("banuser") & filters.private)
    async def ban_user_cmd(client: Client, message: Message):
        if message.from_user.id != config.ADMIN_ID:
            return

        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.reply(
                "Usage: `/banuser <user_id> <message>`\n"
                "Example: `/banuser 123456789 You have been suspended.`",
                parse_mode="markdown",
            )
            return

        try:
            user_id = int(parts[1].strip())
            ban_message = parts[2].strip()
            await db.ban_user(user_id, ban_message)

            try:
                await client.send_message(user_id, f"🚫 {ban_message}")
            except Exception:
                pass

            await message.reply(f"✅ کاربر `{user_id}` بن شد.", parse_mode="markdown")
        except ValueError:
            await message.reply("❌ Invalid user ID.")

    @app.on_message(filters.command("unbanuser") & filters.private)
    async def unban_user_cmd(client: Client, message: Message):
        if message.from_user.id != config.ADMIN_ID:
            return

        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("Usage: `/unbanuser <user_id>`", parse_mode="markdown")
            return

        try:
            user_id = int(parts[1].strip())
            await db.unban_user(user_id)

            try:
                await client.send_message(user_id, "✅ Your access has been restored.")
            except Exception:
                pass

            await message.reply(f"✅ کاربر `{user_id}` رفع بن شد.", parse_mode="markdown")
        except ValueError:
            await message.reply("❌ Invalid user ID.")

    @app.on_message(filters.command("setlimit") & filters.private)
    async def set_limit_cmd(client: Client, message: Message):
        if message.from_user.id != config.ADMIN_ID:
            return

        parts = message.text.split()
        if len(parts) != 5:
            await message.reply(
                "Usage: `/setlimit <user_id> <max_file_mb> <daily_mb> <queue_limit>`\n"
                "Use `0` for any value to reset to default.\n"
                "Example: `/setlimit 123456789 1024 5120 5`",
                parse_mode="markdown",
            )
            return

        try:
            user_id = int(parts[1])
            max_file = int(parts[2]) or None
            daily = int(parts[3]) or None
            queue = int(parts[4]) or None
            await db.set_user_limit(user_id, max_file, daily, queue)
            await message.reply(
                f"✅ محدودیت‌های `{user_id}` به‌روز شد:\n"
                f"  حداکثر فایل: `{max_file or 'پیش‌فرض'} MB`\n"
                f"  روزانه: `{daily or 'پیش‌فرض'} MB`\n"
                f"  صف: `{queue or 'پیش‌فرض'}`",
                parse_mode="markdown",
            )
        except ValueError:
            await message.reply("❌ همه مقادیر باید عدد صحیح باشند.")
