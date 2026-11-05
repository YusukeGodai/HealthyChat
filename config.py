"""OpenAI-compatible defaults, with optional local configuration."""
import json
import os
from pathlib import Path
import sys

# For a packaged app, keep editable config alongside the executable.
CONFIG_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
LOCAL_CONFIG_PATH = CONFIG_DIR / "config.local.json"
local_config = {}
if LOCAL_CONFIG_PATH.exists():
    try:
        local_config = json.loads(LOCAL_CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(local_config, dict):
            raise ValueError("expected object")
    except (OSError, ValueError):
        raise RuntimeError("无法读取 config.local.json，请检查 JSON 格式。") from None

DEFAULT_API_BASE = os.environ.get("HEALTHYCHAT_API_BASE", local_config.get("api_base", "https://edge.gpt.rmqg.org/v1"))
DEFAULT_MODEL = os.environ.get("HEALTHYCHAT_MODEL", local_config.get("model", "gpt-5.6-sol"))
DEFAULT_API_KEY = os.environ.get("HEALTHYCHAT_API_KEY", local_config.get("api_key", ""))
