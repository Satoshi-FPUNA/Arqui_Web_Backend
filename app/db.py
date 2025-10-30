from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

# Toma la URL de la base de datos desde el .env
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./cafeteria.db")

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}      # SQLite, por seguridad, solo permite un hilo de acceso por conexión.

engine = create_engine(DB_URL, echo=False, connect_args=connect_args)

# Función para crear las tablas
def init_db():
    from . import models  # asegura que las clases estén cargadas
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
