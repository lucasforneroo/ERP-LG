from fastapi import APIRouter, HTTPException

router = APIRouter()

ordenes_db = {}
anticipos_db = {}
of_counter = 0
anticipo_counter = 0


@router.get("/")
async def get_comercial_status():
    return {"module": "Comercial", "status": "active"}


@router.get("/ordenes-fabricacion")
async def list_ordenes():
    return {"data": list(ordenes_db.values())}


@router.post("/ordenes-fabricacion")
async def create_of(payload: dict):
    global of_counter, anticipo_counter
    of_counter += 1
    orden = {"id": of_counter, **payload, "estado": "pendiente_anticipo"}
    ordenes_db[of_counter] = orden

    anticipo_counter += 1
    anticipo = {
        "id": anticipo_counter,
        "of_id": of_counter,
        "cliente": payload.get("cliente", ""),
        "monto_estimado": payload.get("monto_anticipo", 0),
        "estado": "pendiente",
        "factura_pago": None,
        "pagado": False,
    }
    anticipos_db[anticipo_counter] = anticipo

    return {
        "message": "OF creada. Anticipo pendiente de validación por Administración",
        "data": {"orden": orden, "anticipo": anticipo},
    }


@router.get("/ordenes-fabricacion/{of_id}")
async def get_of(of_id: int):
    if of_id not in ordenes_db:
        raise HTTPException(status_code=404, detail=f"OF {of_id} no encontrada")
    return {"data": ordenes_db[of_id]}


@router.get("/anticipos")
async def list_anticipos():
    return {"data": list(anticipos_db.values())}
