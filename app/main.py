from fastapi import FastAPI
from .db import init_db
from .routers import clients, rules, expirations, concepts, pointsbag, pointsuse
from .core.scheduler import start_scheduler, shutdown_scheduler
from app.routers import loyalty_levels

app = FastAPI(title="Galletita Cafetería")


@app.on_event("startup")
def startup():
    init_db()
    start_scheduler(app)   # inicia tarea diaria

@app.on_event("shutdown")
def shutdown():
    shutdown_scheduler(app)  # apaga scheduler limpio

app.include_router(clients.router)
app.include_router(rules.router)
app.include_router(expirations.router)
app.include_router(concepts.router)
app.include_router(pointsbag.router)
app.include_router(pointsuse.router)
app.include_router(loyalty_levels.router)