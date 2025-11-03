from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()  # lee .env

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Fidelización")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"
MAIL_USE_CREDENTIALS = os.getenv("MAIL_USE_CREDENTIALS", "True").lower() == "true"
MAIL_VALIDATE_CERTS = os.getenv("MAIL_VALIDATE_CERTS", "True").lower() == "true"

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_STARTTLS=MAIL_STARTTLS,
    MAIL_SSL_TLS=MAIL_SSL_TLS,
    USE_CREDENTIALS=MAIL_USE_CREDENTIALS,
    VALIDATE_CERTS=MAIL_VALIDATE_CERTS,
)

class PointsAssignedEmail(BaseModel):
    to: EmailStr
    nombre: str
    puntos_asignados: int
    saldo_puntos: int
    fecha_caducidad: str   # YYYY-MM-DD
    monto_operacion: int

async def send_points_assigned_email(data: PointsAssignedEmail):
    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif">
      <h2>¡Puntos acreditados!</h2>
      <p>Hola <b>{data.nombre}</b>,</p>
      <p>Te acreditamos <b>{data.puntos_asignados} puntos</b> por tu compra de <b>Gs. {data.monto_operacion:,}</b>.</p>
      <p><b>Vencimiento:</b> {data.fecha_caducidad}</p>
      <p><b>Saldo actual:</b> {data.saldo_puntos} puntos</p>
      <hr/>
      <small>Gracias por tu preferencia.</small>
    </div>
    """

    message = MessageSchema(
        subject="Puntos acreditados - Programa de Fidelización",
        recipients=[data.to],
        body=html,
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    
def mail() -> FastMail:
    return FastMail(conf)

class PointsExpiringItem(BaseModel):
    fecha_caducidad: str  # "YYYY-MM-DD"
    puntos: int

# correo: puntos próximos a vencer
async def send_points_expiring_email(
    to_email: EmailStr,
    cliente_nombre: str,
    items: List[PointsExpiringItem]
):
    if not to_email or not items:
        return

    # construir el detalle y total
    total = sum(i.puntos for i in items)
    lines = "<br>".join(
        f"- {i.puntos} puntos vencen el {i.fecha_caducidad}" for i in items
    )

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif">
      <h3>¡Atención, {cliente_nombre}!</h3>
      <p>Tienes puntos próximos a vencer:</p>
      <p>{lines}</p>
      <p><b>Total por vencer:</b> {total} puntos.</p>
      <hr/>
      <small>Usa tus beneficios antes del vencimiento.</small>
    </div>
    """

    message = MessageSchema(
        subject="Aviso: puntos próximos a vencer",
        recipients=[to_email],
        body=html,
        subtype="html",
    )
    await mail().send_message(message)