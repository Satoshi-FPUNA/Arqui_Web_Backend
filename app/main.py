from fastapi import FastAPI
from .db import init_db
from .routers import clients, rules, expirations,concepts

app = FastAPI(title="Galletita Cafetería")

@app.on_event("startup")
def startup():
    init_db()

app.include_router(clients.router)
app.include_router(rules.router)
app.include_router(expirations.router)
app.include_router(concepts.router)