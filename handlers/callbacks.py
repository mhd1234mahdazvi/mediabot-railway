from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

import database as db
import config
from handlers.message import get_pending, remove_pending, dispatch_download


def register(app: Client):

    @app.on_callback_query(filters.regex(r"^quality:(.+):(.+)$"))
    async def quality_selected(client: Client, callback: CallbackQuery):
        _, job_id, quality = callback.data.split(":", 2)
        user_id = callback.from_user.id

        job = get_pending(job_id)
        if not job:
            await callback.answer("❌ نشست منقضی شده. لطفاً لینک را دوباره بفرستید.", show_alert=True)
            await callback.message.delete()
            return

        if job.telegram_id != user_id:
            await callback.answer("❌ این دانلود مربوط به شما نیست.", show_alert=True)
            return

        await callback.message.edit_text(config.MSG_DOWNLOAD_START)
        await callback.answer()

        await dispatch_download(client, job, quality, callback.message)

    @app.on_callback_query(filters.regex(r"^cancel:(.+)$"))
    async def cancel_pending(client: Client, callback: CallbackQuery):
        _, job_id = callback.data.split(":", 1)
        user_id = callback.from_user.id

        job = get_pending(job_id)
        if job and job.telegram_id == user_id:
            remove_pending(job_id)
            await callback.message.edit_text("🚫 لغو شد.")
        else:
            await callback.answer("چیزی برای لغو وجود ندارد.", show_alert=True)

        await callback.answer()
