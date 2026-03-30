"""
Lightweight Ollama availability probe (avoids LLM calls when server is down).
"""
import time
import urllib.error
import urllib.request

from src.config import ollama_native_base_url

_last_ok = False
_last_check = 0.0
_CACHE_TTL_SEC = 5.0


def ollama_is_reachable(timeout_sec: float = 1.5) -> bool:
    global _last_ok, _last_check
    now = time.monotonic()
    if now - _last_check < _CACHE_TTL_SEC and _last_check > 0:
        return _last_ok
    _last_check = now
    url = f"{ollama_native_base_url()}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as resp:
            _last_ok = 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        _last_ok = False
    return _last_ok
