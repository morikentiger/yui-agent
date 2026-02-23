"""
YUi Configuration

.envファイルまたは環境変数から設定を読み込む。
OpenRouter経由でClaude等のLLMを利用。
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

_env_loaded = False


def load_env():
    """プロジェクトルートの.envファイルから環境変数を読み込む"""
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True

    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value:
                    os.environ[key] = value


def get_gemini_api_key() -> str:
    """Gemini APIキーを取得。"""
    load_env()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set.\n"
            f"Create {ENV_FILE} with:\n"
            "  GEMINI_API_KEY=AIza..."
        )
    return key


def get_openrouter_api_key() -> str:
    """OpenRouter APIキーを取得（バックアップ用）。"""
    load_env()
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set.\n"
            f"Create {ENV_FILE} with:\n"
            "  OPENROUTER_API_KEY=sk-or-..."
        )
    return key


def get_honcho_api_key() -> str | None:
    """Honcho APIキーを取得。なければNone。"""
    load_env()
    key = os.environ.get("HONCHO_API_KEY", "").strip()
    return key if key else None


def get_honcho_base_url() -> str:
    """Honcho API URLを取得。"""
    load_env()
    return os.environ.get("HONCHO_BASE_URL", "https://api.honcho.dev").strip()
