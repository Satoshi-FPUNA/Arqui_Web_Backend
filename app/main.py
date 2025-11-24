from fastapi import FastAPI
from .db import init_db
from .routers import clients, rules, expirations, concepts, pointsbag, pointsuse, surveys, dashboard 
from .core.scheduler import start_scheduler, shutdown_scheduler
from app.routers import loyalty_levels
<<<<<<< HEAD
=======
from app.routers import products
from app.routers import redeem

from .routers import surveys
>>>>>>> e2521e1439df1508f5cf0c25369935a76752b911

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
<<<<<<< HEAD
app.include_router(surveys.router)
app.include_router(dashboard.router)
=======
app.include_router(products.router)
app.include_router(redeem.router)
app.include_router(surveys.router)
>>>>>>> e2521e1439df1508f5cf0c25369935a76752b911
