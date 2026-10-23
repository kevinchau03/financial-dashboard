"""Local settings; deployed environment variables always take precedence."""
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / '.env.local', override=False)


def database_url() -> str:
    value = os.getenv('DATABASE_URL', '').strip()
    on_vercel = os.getenv('VERCEL') == '1' or os.getenv('VERCEL_ENV') in ('production', 'preview')
    if on_vercel and not value:
        raise ValueError('DATABASE_URL is required in the Vercel backend project environment. Set the Supabase PostgreSQL connection URL and redeploy.')
    if on_vercel and value.split(':', 1)[0].split('+', 1)[0] not in ('postgres', 'postgresql'):
        raise ValueError('DATABASE_URL must use PostgreSQL on Vercel. SQLite is only supported for local development and tests.')
    return value or f"sqlite:///{(BACKEND_DIR / 'goals.db').as_posix()}"


def auth_settings() -> tuple[str, str]:
    url = os.getenv('SUPABASE_URL', '').rstrip('/')
    key = os.getenv('SUPABASE_PUBLISHABLE_KEY', '')
    if not url.startswith('https://') or not key.startswith('sb_publishable_'):
        raise ValueError('Set SUPABASE_URL and a Supabase publishable key in backend/.env.local.')
    return url, key
