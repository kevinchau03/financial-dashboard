from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from app.auth import get_current_user
from app.config import auth_settings
from app.database import engine
from app.startup import initialize_database
from app.routers import accounts, goals, bills, debts, paycheques, statements, analytics, uploads, payments

@asynccontextmanager
async def lifespan(app: FastAPI):
    if engine.dialect.name == 'sqlite':
        initialize_database(engine)
    yield

app = FastAPI(lifespan=lifespan)
for router_module in (accounts, goals, bills, debts, paycheques, statements, analytics, uploads, payments):
    app.include_router(router_module.router, dependencies=[Depends(get_current_user)])

@app.middleware('http')
async def private_responses(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.get('/api/auth/config')
def public_auth_config():
    try:
        url, key = auth_settings()
    except ValueError:
        raise HTTPException(503, 'Authentication is not configured. Set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY in backend/.env.local.') from None
    return {'url': url, 'publishable_key': key}

@app.get('/api/auth/me')
def me(user=Depends(get_current_user)):
    return {'id': str(user.id), 'email': user.email}
