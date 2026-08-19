import asyncio
import uuid
import os
import shutil
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable
from datetime import datetime

import config
import database as db

os.makedirs(config.TEMP_DIR, exist_ok=True)


@dataclass
class DownloadJob:
    job_id: str
    telegram_id: int
    url: str
    platform: str
    quality: Optional[str]          # "1080p" | "720p" | "480p" | "audio"
    chat_id: int
    message_id: int                 # status message to edit
    created_at: datetime = field(default_factory=datetime.utcnow)
    file_path: Optional[str] = None
    file_size_mb: float = 0.0
    status: str = "queued"          # queued | downloading | uploading | done | failed | cancelled


# per-user active job count tracker (in-memory, fast)
_user_active: dict[int, int] = {}
_user_queues: dict[int, asyncio.Queue] = {}
_global_semaphore: asyncio.Semaphore = None


def _get_semaphore() -> asyncio.Semaphore:
    global _global_semaphore
    if _global_semaphore is None:
        _global_semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_DOWNLOADS)
    return _global_semaphore


def get_user_active_count(telegram_id: int) -> int:
    return _user_active.get(telegram_id, 0)


def _increment_user_active(telegram_id: int):
    _user_active[telegram_id] = _user_active.get(telegram_id, 0) + 1


def _decrement_user_active(telegram_id: int):
    count = _user_active.get(telegram_id, 0)
    _user_active[telegram_id] = max(0, count - 1)


async def enqueue(
    job: DownloadJob,
    download_fn: Callable[[DownloadJob], Awaitable[bool]],
    on_done: Callable[[DownloadJob], Awaitable[None]],
) -> bool:
    """
    Enqueue a download job. Returns False if user's queue is full.
    download_fn(job) -> bool: performs the actual download, sets job.file_path and job.file_size_mb
    on_done(job): called after download+upload cycle completes (success or fail)
    """
    limits = await db.get_user_limits(job.telegram_id)
    queue_limit = limits["queue_limit"]

    if get_user_active_count(job.telegram_id) >= queue_limit:
        return False

    _increment_user_active(job.telegram_id)
    asyncio.create_task(_run_job(job, download_fn, on_done, limits))
    return True


async def _run_job(
    job: DownloadJob,
    download_fn: Callable[[DownloadJob], Awaitable[bool]],
    on_done: Callable[[DownloadJob], Awaitable[None]],
    limits: dict,
):
    sem = _get_semaphore()
    async with sem:
        try:
            job.status = "downloading"
            success = await download_fn(job)

            if not success:
                job.status = "failed"
                await db.log_download(job.telegram_id, job.url, job.platform, 0.0, "failed")
                await on_done(job)
                return

            # file size check (post-download, exact size)
            if job.file_path and os.path.exists(job.file_path):
                actual_mb = os.path.getsize(job.file_path) / (1024 * 1024)
                job.file_size_mb = actual_mb

                if actual_mb > limits["max_file_mb"]:
                    job.status = "failed_size"
                    _cleanup_job_file(job)
                    await db.log_download(job.telegram_id, job.url, job.platform, actual_mb, "failed")
                    await on_done(job)
                    return

                # daily limit check
                used_mb = await db.get_daily_usage_mb(job.telegram_id)
                if used_mb + actual_mb > limits["daily_limit_mb"]:
                    job.status = "failed_daily"
                    _cleanup_job_file(job)
                    await db.log_download(job.telegram_id, job.url, job.platform, actual_mb, "failed")
                    await on_done(job)
                    return

            job.status = "uploading"
            await on_done(job)

        except asyncio.CancelledError:
            job.status = "cancelled"
            _cleanup_job_file(job)
            await db.log_download(job.telegram_id, job.url, job.platform, 0.0, "cancelled")
            await on_done(job)

        except Exception as e:
            job.status = "failed"
            _cleanup_job_file(job)
            await db.log_download(job.telegram_id, job.url, job.platform, 0.0, "failed")
            await on_done(job)

        finally:
            _decrement_user_active(job.telegram_id)


def _cleanup_job_file(job: DownloadJob):
    if job.file_path and os.path.exists(job.file_path):
        try:
            if os.path.isdir(job.file_path):
                shutil.rmtree(job.file_path)
            else:
                os.remove(job.file_path)
        except OSError:
            pass


def make_job_dir(job_id: str) -> str:
    path = os.path.join(config.TEMP_DIR, job_id)
    os.makedirs(path, exist_ok=True)
    return path
