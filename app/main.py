from fastapi import FastAPI
from .db import init_db
from .routers import clients, rules, expirations, concepts

# Crear instancia principal de FastAPI
app = FastAPI(
    title="Cafetería Loyalty API",
    description="Backend del sistema de puntos de fidelización para la cafetería.",
    version="1.0.0"
)

# Inicializa la base de datos al iniciar el servidor
@app.on_event("startup")
def on_startup():
    init_db()

# Registrar routers (rutas agrupadas)
app.include_router(clients.router)
app.include_router(rules.router)
app.include_router(expirations.router)
app.include_router(concepts.router)

# Ruta de prueba / raíz
@app.get("/")
def root():
    return {"message": "☕ Bienvenido a la API de la Cafetería"}