"""Local settings; deployed environment variables always take precedence."""
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / '.env.local', override=False)


def auth_settings() -> tuple[str, str]:
    url = os.getenv('SUPABASE_URL', '').rstrip('/')
    key = os.getenv('SUPABASE_PUBLISHABLE_KEY', '')
    if not url.startswith('https://') or not key.startswith('sb_publishable_'):
        raise ValueError('Set SUPABASE_URL and a Supabase publishable key in backend/.env.local.')
    return url, key
