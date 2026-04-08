from fastapi import APIRouter, HTTPException
from app.api.v1.endpoints.comercial import anticipos_db, ordenes_db

router = APIRouter()

pedidos_db = {}
planos_db = {}
pedido_counter = 0
plano_counter = 0


def verificar_of_aprobada(of_id):
    if of_id not in ordenes_db:
        raise HTTPException(status_code=404, detail=f"OF {of_id} no encontrada")
    orden = ordenes_db[of_id]
    if orden["estado"] != "aprobada":
        anticipo = next(
            (a for a in anticipos_db.values() if a["of_id"] == of_id), None
        )
        estado_anticipo = anticipo["estado"] if anticipo else "sin anticipo"
        raise HTTPException(
            status_code=403,
            detail=f"OF {of_id} no disponible. Estado: {orden['estado']}. Anticipo: {estado_anticipo}",
        )


@router.get("/")
async def get_desarrollo_status():
    return {"module": "Desarrollo", "status": "active"}


@router.get("/ordenes-disponibles")
async def list_ordenes_disponibles():
    disponibles = [o for o in ordenes_db.values() if o["estado"] == "aprobada"]
    return {"data": disponibles}


@router.post("/pedidos-material")
async def create_pedido_material(payload: dict):
    global pedido_counter
    of_id = payload.get("of_id")
    if of_id:
        verificar_of_aprobada(int(of_id))

    pedido_counter += 1
    pedido = {"id": pedido_counter, **payload, "estado": "generado"}
    pedidos_db[pedido_counter] = pedido
    return {"message": "Pedido de materiales generado", "data": pedido}


@router.get("/pedidos-material")
async def list_pedidos():
    return {"data": list(pedidos_db.values())}


@router.post("/planos")
async def create_plano(payload: dict):
    global plano_counter
    of_id = payload.get("of_id")
    if of_id:
        verificar_of_aprobada(int(of_id))

    plano_counter += 1
    plano = {"id": plano_counter, **payload, "estado": "enviado"}
    planos_db[plano_counter] = plano
    return {"message": "Plano enviado a Producción", "data": plano}


@router.get("/planos")
async def list_planos():
    return {"data": list(planos_db.values())}
