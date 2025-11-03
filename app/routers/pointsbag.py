from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from app.db import engine
from app.models import PointsBag, Client, Rule, Expiration, PointConcept
from datetime import date, timedelta

router = APIRouter(prefix="/pointsbag", tags=["Bolsa de Puntos"])

# 🔹 Listar todas las bolsas
@router.get("/")
def list_points_bags():
    with Session(engine) as session:
        bolsas = session.exec(select(PointsBag)).all()
        return bolsas

# 🔹 Crear una nueva bolsa (asignar puntos)
@router.post("/")
def create_points_bag(cliente_id: int, monto_operacion: int):
    today = date.today()
    with Session(engine) as session:
        # 🔹 Verificar si el cliente existe
        cliente = session.get(Client, cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # 🔹 Buscar la regla aplicable según el monto
        regla = session.exec(
            select(Rule)
            .where(Rule.limite_inferior <= monto_operacion)
            .where((Rule.limite_superior == None) | (Rule.limite_superior >= monto_operacion))
        ).first()

        if not regla:
            raise HTTPException(status_code=400, detail="No hay una regla aplicable para este monto.")

        # Calcular puntos según la equivalencia de la regla
        puntos_asignados = monto_operacion // regla.equivalencia_monto

        # 🔹 Buscar la duración vigente en la tabla Expiration
        expiracion = session.exec(
            select(Expiration)
            .where(Expiration.fecha_inicio_validez <= today)
            .where(Expiration.fecha_fin_validez >= today)
        ).first()

        # Si hay configuración, usarla; si no, aplicar un valor por defecto (30 días)
        dias_duracion = expiracion.dias_duracion if expiracion else 30
        fecha_asignacion = today
        fecha_caducidad = fecha_asignacion + timedelta(days=dias_duracion)

        # 🔹 Crear la nueva bolsa
        nueva_bolsa = PointsBag(
            cliente_id=cliente_id,
            fecha_asignacion=fecha_asignacion,
            fecha_caducidad=fecha_caducidad,
            puntos_asignados=puntos_asignados,
            puntos_utilizados=0,
            saldo_puntos=puntos_asignados,
            monto_operacion=monto_operacion
        )

        session.add(nueva_bolsa)
        session.commit()
        session.refresh(nueva_bolsa)

        return {
            "mensaje": "Bolsa creada correctamente",
            "cliente_id": cliente_id,
            "monto_operacion": monto_operacion,
            "puntos_asignados": puntos_asignados,
            "fecha_caducidad": fecha_caducidad,
            "dias_duracion": dias_duracion,
            "regla_aplicada": {
                "id": regla.id,
                "limite_inferior": regla.limite_inferior,
                "limite_superior": regla.limite_superior,
                "equivalencia_monto": regla.equivalencia_monto
            }
        }

# 🔹 Ver bolsas de un cliente específico
@router.get("/cliente/{cliente_id}")
def get_all_bags_with_status(cliente_id: int):
    today = date.today()
    with Session(engine) as session:
        bolsas = session.exec(
            select(PointsBag).where(PointsBag.cliente_id == cliente_id)
        ).all()

        if not bolsas:
            raise HTTPException(status_code=404, detail="El cliente no tiene bolsas registradas")

        total_vigentes = 0
        bolsas_respuesta = []

        for b in bolsas:
            estado = "vigente" if b.fecha_caducidad >= today else "vencida"

            if estado == "vigente":
                total_vigentes += b.saldo_puntos

            bolsas_respuesta.append({
                "id": b.id,
                "fecha_asignacion": b.fecha_asignacion,
                "fecha_caducidad": b.fecha_caducidad,
                "puntos_asignados": b.puntos_asignados,
                "puntos_utilizados": b.puntos_utilizados,
                "saldo_puntos": b.saldo_puntos,
                "monto_operacion": b.monto_operacion,
                "estado": estado
            })

        return {
            "cliente_id": cliente_id,
            "total_puntos_vigentes": total_vigentes,
            "bolsas": bolsas_respuesta
        }

# 🔹 Actualizar una bolsa (por ejemplo, si se usan puntos)
@router.put("/{bag_id}")
def update_points_bag(bag_id: int, puntos_usados: int):
    with Session(engine) as session:
        bolsa = session.get(PointsBag, bag_id)
        if not bolsa:
            raise HTTPException(status_code=404, detail="Bolsa no encontrada")

        if bolsa.fecha_caducidad < date.today():
            raise HTTPException(status_code=400, detail="Esta bolsa está vencida y no puede usarse.")

        if bolsa.saldo_puntos < puntos_usados:
            raise HTTPException(status_code=400, detail="Saldo insuficiente")

        bolsa.puntos_utilizados += puntos_usados
        bolsa.saldo_puntos -= puntos_usados

        session.add(bolsa)
        session.commit()
        session.refresh(bolsa)
        return bolsa

# 🔹 Usar puntos (canje FIFO + registro de canje)
@router.put("/cliente/{cliente_id}/usar")
def use_points(cliente_id: int, concepto_id: int):
    from datetime import date
    with Session(engine) as session:
        # 🔹 Buscar el concepto del canje (ej: "Café gratis")
        from app.models import PointConcept, PointsUseHeader, PointsUseDetail
        concepto = session.get(PointConcept, concepto_id)
        if not concepto:
            raise HTTPException(status_code=404, detail="Concepto no encontrado")

        # 🔹 Tomar automáticamente los puntos requeridos desde el concepto
        puntos_a_usar = concepto.puntos_requeridos
        puntos_restantes = puntos_a_usar
        movimientos = []

        # 🔹 Buscar bolsas vigentes con saldo
        bolsas = session.exec(
            select(PointsBag)
            .where(PointsBag.cliente_id == cliente_id)
            .where(PointsBag.fecha_caducidad >= date.today())
            .where(PointsBag.saldo_puntos > 0)
            .order_by(PointsBag.fecha_caducidad)
        ).all()

        if not bolsas:
            raise HTTPException(status_code=404, detail="El cliente no tiene puntos vigentes")

        # 🔹 Descontar puntos de las bolsas (FIFO)
        for bolsa in bolsas:
            if puntos_restantes <= 0:
                break

            puntos_a_descontar = min(bolsa.saldo_puntos, puntos_restantes)
            bolsa.saldo_puntos -= puntos_a_descontar
            bolsa.puntos_utilizados += puntos_a_descontar

            movimientos.append({
                "bolsa_id": bolsa.id,
                "puntos_usados": puntos_a_descontar,
                "fecha_caducidad": bolsa.fecha_caducidad
            })

            puntos_restantes -= puntos_a_descontar
            session.add(bolsa)

        # 🔹 Si no alcanza el saldo, cancelar operación
        if puntos_restantes > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo insuficiente. Faltan {puntos_restantes} puntos para completar el canje."
            )

        # 🔹 Crear cabecera del canje
        cabecera = PointsUseHeader(
            cliente_id=cliente_id,
            puntaje_utilizado=puntos_a_usar,
            fecha=date.today(),
            concepto_id=concepto_id
        )
        session.add(cabecera)
        session.commit()
        session.refresh(cabecera)

        # 🔹 Crear detalles del canje (una fila por cada bolsa usada)
        for mov in movimientos:
            detalle = PointsUseDetail(
                cabecera_id=cabecera.id,
                puntaje_utilizado=mov["puntos_usados"],
                bolsa_id=mov["bolsa_id"]
            )
            session.add(detalle)

        session.commit()

        return {
            "cliente_id": cliente_id,
            "concepto": concepto.descripcion,
            "puntos_usados": puntos_a_usar,
            "detalle_movimiento": movimientos,
            "registro": {
                "cabecera_id": cabecera.id,
                "fecha": cabecera.fecha
            }
        }


# 🔹 Eliminar una bolsa (opcional)
@router.delete("/{bag_id}")
def delete_points_bag(bag_id: int):
    with Session(engine) as session:
        bolsa = session.get(PointsBag, bag_id)
        if not bolsa:
            raise HTTPException(status_code=404, detail="Bolsa no encontrada")
        session.delete(bolsa)
        session.commit()
        return {"ok": True, "mensaje": "Bolsa eliminada correctamente"}
