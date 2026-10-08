from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine
from app.startup import initialize_database
from app.routers import accounts, goals, bills, debts, paycheques, statements, analytics, uploads

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database(engine)
    yield

app = FastAPI(lifespan=lifespan)
for router_module in (accounts, goals, bills, debts, paycheques, statements, analytics, uploads):
    app.include_router(router_module.router)

@app.get("/")
def read_root():
    return {"Hello": "Kevin"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
