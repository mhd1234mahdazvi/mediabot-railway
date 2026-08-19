import os
import asyncio
from typing import Optional

import yt_dlp

from .base import BasePlugin


class TikTokPlugin(BasePlugin):
    PLATFORM_NAME = "tiktok"
    SUPPORTED_DOMAINS = ["tiktok.com", "www.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"]
    PRIORITY = 10

    QUALITY_OPTIONS = [
        {"label": "🎬 Best Quality (No Watermark)", "value": "best"},
        {"label": "🎵 Audio Only",                  "value": "audio"},
    ]

    def _opts(self, dest_dir: str, quality: str) -> dict:
        opts = {
            "format": "bestvideo+bestaudio/best" if quality != "audio" else "bestaudio",
            "outtmpl": os.path.join(dest_dir, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "merge_output_format": "mp4",
            "socket_timeout": 30,
            # attempt watermark-free download
            "extractor_args": {"tiktok": {"webpage_download": ["1"]}},
        }
        if quality == "audio":
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        return opts

    async def get_info(self, url: str) -> Optional[dict]:
        def _fetch():
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.get_event_loop().run_in_executor(None, _fetch)
            return {
                "title": info.get("description") or info.get("title") or "TikTok Video",
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "platform": self.PLATFORM_NAME,
                "has_video": True,
                "has_audio": True,
            }
        except Exception:
            return None

    async def download(self, url: str, quality: str, dest_dir: str) -> Optional[str]:
        if quality not in ("audio",):
            quality = "best"

        opts = self._opts(dest_dir, quality)

        def _do_download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        try:
            filename = await asyncio.get_event_loop().run_in_executor(None, _do_download)
            if not os.path.exists(filename):
                files = os.listdir(dest_dir)
                if files:
                    filename = os.path.join(dest_dir, files[0])
                else:
                    return None
            return filename
        except Exception:
            return None
