from abc import ABC, abstractmethod
from typing import Optional


class BasePlugin(ABC):
    """
    Every platform plugin inherits this.
    Implement all abstract methods. PLATFORM_NAME and SUPPORTED_DOMAINS are required.
    """

    PLATFORM_NAME: str = "unknown"
    SUPPORTED_DOMAINS: list[str] = []
    PRIORITY: int = 0           # higher = checked first; set higher for specific platforms

    QUALITY_OPTIONS: list[dict] = [
        {"label": "🎬 1080p",     "value": "1080p"},
        {"label": "🎬 720p",      "value": "720p"},
        {"label": "🎬 480p",      "value": "480p"},
        {"label": "🎵 Audio Only","value": "audio"},
    ]

    def can_handle_sync(self, url: str) -> bool:
        """Fast sync domain check — used for routing."""
        return any(domain in url for domain in self.SUPPORTED_DOMAINS)

    async def can_handle(self, url: str) -> bool:
        """Async version — override if you need network validation."""
        return self.can_handle_sync(url)

    @abstractmethod
    async def get_info(self, url: str) -> Optional[dict]:
        """
        Return metadata dict without downloading:
        {
            "title": str,
            "thumbnail": str | None,
            "duration": int | None,   # seconds
            "platform": str,
            "has_video": bool,
            "has_audio": bool,
        }
        Returns None if URL is invalid or unreachable.
        """
        ...

    @abstractmethod
    async def download(self, url: str, quality: str, dest_dir: str) -> Optional[str]:
        """
        Download media to dest_dir. Returns the full path of the downloaded file.
        quality: "1080p" | "720p" | "480p" | "audio"
        Returns None on failure.
        """
        ...

    def quality_supports_video(self, quality: str) -> bool:
        return quality != "audio"

    def get_quality_options(self) -> list[dict]:
        """Override to restrict quality options for this platform."""
        return self.QUALITY_OPTIONS
