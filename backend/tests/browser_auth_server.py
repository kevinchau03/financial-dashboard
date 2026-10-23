"""Disposable browser fixture: no real Supabase credentials, users or data.

Run from backend: uv run python tests/browser_auth_server.py
Use owner@example.test / password12, or second@example.test / password12.
Only binds localhost. Closing the process removes its temporary SQLite database.
"""
import base64
from pathlib import Path
import sys
import tempfile
import time
import json
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import httpx
import uvicorn
from fastapi import Request, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from app import main, auth, database


def encode(value):
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('=')


def run():
    with tempfile.TemporaryDirectory(prefix='budget-auth-browser-') as directory:
        engine = database.build_engine(f'sqlite:///{Path(directory).as_posix()}/test.db')
        main.engine = database.engine = engine
        settings = lambda: ('http://127.0.0.1:8011', 'sb_publishable_local_browser_test')
        main.auth_settings = auth.auth_settings = settings
        state = {'expired': False, 'unavailable': False, 'slow': False}
        users = {
            email: {'id': f'00000000-0000-4000-8000-00000000000{index}',
                    'email': email, 'aud': 'authenticated', 'role': 'authenticated',
                    'created_at': '2026-01-01T00:00:00Z', 'app_metadata': {}, 'user_metadata': {}}
            for index, email in enumerate(('owner@example.test', 'second@example.test'), 1)
        }
        tokens = {}

        def verify(request):
            if state['unavailable']:
                return httpx.Response(503)
            token = request.headers.get('authorization', '').removeprefix('Bearer ')
            user = tokens.get(token)
            return httpx.Response(200, json=user) if user and not state['expired'] else httpx.Response(401)

        with httpx.Client(transport=httpx.MockTransport(verify)) as provider:
            auth.auth_client = lambda: provider

            @main.app.post('/auth/v1/token')
            async def token(request: Request):
                payload = await request.json()
                if state['slow']:
                    await asyncio.sleep(2)
                if state['unavailable']:
                    raise HTTPException(503, 'Fixture unavailable')
                user = users.get(payload.get('email'))
                if not user or payload.get('password') != 'password12':
                    return Response(json.dumps({'error': 'invalid_grant', 'error_description': 'Invalid login credentials'}), status_code=400, media_type='application/json')
                state['expired'] = False
                now = int(time.time())
                access = f"{encode({'alg': 'HS256', 'typ': 'JWT'})}.{encode({'sub': user['id'], 'aud': 'authenticated', 'iat': now, 'exp': now + 3600})}.browser-fixture"
                tokens[access] = user
                return {'access_token': access, 'refresh_token': 'browser-fixture-refresh',
                        'expires_in': 3600, 'token_type': 'bearer', 'user': user}

            @main.app.post('/auth/v1/logout')
            def logout():
                return Response(status_code=204)

            @main.app.get('/__fixture/{mode}')
            def control(mode: str):
                if mode == 'expire': state['expired'] = True
                elif mode == 'offline': state['unavailable'] = True
                elif mode == 'online': state['unavailable'] = False
                elif mode == 'slow': state['slow'] = True
                elif mode == 'fast': state['slow'] = False
                else: raise HTTPException(404)
                return {'mode': mode}

            main.app.mount('/', StaticFiles(directory=Path(__file__).resolve().parents[2] / 'frontend/dist', html=True), name='browser-fixture')
            uvicorn.run(main.app, host='127.0.0.1', port=8011, log_level='warning', access_log=False)
        engine.dispose()


if __name__ == '__main__':
    run()
