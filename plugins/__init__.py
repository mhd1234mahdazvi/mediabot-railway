"""
Plugin loader — scans the plugins/ directory and loads every module
that contains a class inheriting from BasePlugin.

To add a new platform:
1. Create plugins/mysite.py
2. Define a class MySitePlugin(BasePlugin) with:
   - PLATFORM_NAME: str
   - SUPPORTED_DOMAINS: list[str]
   - async def can_handle(url: str) -> bool
   - async def get_info(url: str, quality: str) -> dict | None
   - async def download(url: str, quality: str, dest_dir: str) -> str | None
3. Done. No other file needs editing.
"""

import importlib
import inspect
import os
import pkgutil
from typing import Optional

from .base import BasePlugin

_plugins: list[BasePlugin] = []


def load_plugins():
    global _plugins
    _plugins = []
    package_dir = os.path.dirname(__file__)

    for _, module_name, _ in pkgutil.iter_modules([package_dir]):
        if module_name in ("__init__", "base"):
            continue
        module = importlib.import_module(f"plugins.{module_name}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                _plugins.append(obj())

    _plugins.sort(key=lambda p: p.PRIORITY, reverse=True)


def get_handler(url: str) -> Optional[BasePlugin]:
    for plugin in _plugins:
        if plugin.can_handle_sync(url):
            return plugin
    return None


async def get_handler_async(url: str) -> Optional[BasePlugin]:
    for plugin in _plugins:
        if await plugin.can_handle(url):
            return plugin
    return None


def list_plugins() -> list[BasePlugin]:
    return _plugins
