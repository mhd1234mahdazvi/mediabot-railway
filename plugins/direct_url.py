import os
import asyncio
import aiohttp
import aiofiles
from typing import Optional
from urllib.parse import urlparse, unquote

from .base import BasePlugin


SUPPORTED_EXTENSIONS = {
    ".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv", ".m4v",
    ".mp3", ".m4a", ".ogg", ".flac", ".wav", ".opus",
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    ".pdf", ".zip",
}


class DirectURLPlugin(BasePlugin):
    PLATFORM_NAME = "direct_url"
    SUPPORTED_DOMAINS = []  # handled by can_handle(), not domain list
    PRIORITY = 0            # lowest priority — fallback only

    QUALITY_OPTIONS = [
        {"label": "⬇️ Download", "value": "best"},
    ]

    def can_handle_sync(self, url: str) -> bool:
        parsed = urlparse(url)
        path = unquote(parsed.path).lower()
        return any(path.endswith(ext) for ext in SUPPORTED_EXTENSIONS)

    async def can_handle(self, url: str) -> bool:
        if self.can_handle_sync(url):
            return True
        # HEAD request to check Content-Type
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    ct = resp.headers.get("Content-Type", "")
                    return any(t in ct for t in ("video/", "audio/", "image/", "application/octet-stream"))
        except Exception:
            return False

    async def get_info(self, url: str) -> Optional[dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    ct = resp.headers.get("Content-Type", "")
                    cl = resp.headers.get("Content-Length")
                    return {
                        "title": os.path.basename(urlparse(url).path) or "file",
                        "thumbnail": None,
                        "duration": None,
                        "platform": self.PLATFORM_NAME,
                        "has_video": "video" in ct,
                        "has_audio": "audio" in ct,
                        "size_bytes": int(cl) if cl else None,
                    }
        except Exception:
            return None

    async def download(self, url: str, quality: str, dest_dir: str) -> Optional[str]:
        parsed = urlparse(url)
        filename = os.path.basename(unquote(parsed.path)) or "download"
        if "." not in filename:
            filename += ".bin"

        dest_path = os.path.join(dest_dir, filename)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                    resp.raise_for_status()
                    async with aiofiles.open(dest_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(1024 * 256):
                            await f.write(chunk)
            return dest_path
        except Exception:
            return None
