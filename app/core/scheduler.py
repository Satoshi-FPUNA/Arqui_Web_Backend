import os
from datetime import date, timedelta
from collections import defaultdict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from sqlmodel import Session, select

from ..models import PointsBag, Client
from ..core.mailer import send_points_expiring_email, PointsExpiringItem
from ..db import engine  # Asegurate de exportar "engine" en app/db.py

load_dotenv()

ALERT_DAYS_BEFORE = int(os.getenv("ALERT_DAYS_BEFORE", "3"))
ALERT_HOUR = int(os.getenv("ALERT_HOUR", "9"))
ALERT_MINUTE = int(os.getenv("ALERT_MINUTE", "0"))

async def _job_points_expiring():
    """Busca bolsas que vencen en los próximos N días y envía emails agrupados por cliente."""
    today = date.today()
    limit = today + timedelta(days=ALERT_DAYS_BEFORE)

    with Session(engine) as session:
        # bolsas con saldo > 0 que vencen dentro de la ventana
        bolsas = session.exec(
            select(PointsBag)
            .where(
                PointsBag.saldo_puntos > 0,
                PointsBag.fecha_caducidad >= today,
                PointsBag.fecha_caducidad <= limit,
            )
        ).all()

        if not bolsas:
            return

        # agrupar por cliente
        por_cliente: dict[int, list[PointsBag]] = defaultdict(list)
        for b in bolsas:
            por_cliente[b.cliente_id].append(b)

        # enviar un correo por cliente
        for cliente_id, lista in por_cliente.items():
            cli = session.get(Client, cliente_id)
            if not cli or not cli.email:
                continue

            items = [
                PointsExpiringItem(
                    fecha_caducidad=str(b.fecha_caducidad),
                    puntos=b.saldo_puntos,
                )
                for b in sorted(lista, key=lambda x: x.fecha_caducidad)
            ]

            await send_points_expiring_email(
                to_email=cli.email,
                cliente_nombre=f"{cli.nombre} {cli.apellido}",
                items=items,
            )

def start_scheduler(app):
    """Arranca el scheduler y lo guarda en app.state."""
    scheduler = AsyncIOScheduler()
    # corre todos los días a la hora configurada
    scheduler.add_job(
        _job_points_expiring,
        CronTrigger(hour=ALERT_HOUR, minute=ALERT_MINUTE),
        id="points_expiring_daily",
        replace_existing=True,
    )
    scheduler.start()
    app.state.scheduler = scheduler

def shutdown_scheduler(app):
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler:
        scheduler.shutdown(wait=False)
