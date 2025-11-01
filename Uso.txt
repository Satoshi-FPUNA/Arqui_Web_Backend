-- Activar entorno virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

-- Instalar librerías necesarias
pip install -r requirements.txt

-- Ejecutar
uvicorn app.main:app --reload

-- Ir a la página
http://127.0.0.1:8000/docs