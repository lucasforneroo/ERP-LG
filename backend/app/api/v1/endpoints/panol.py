from fastapi import APIRouter

router = APIRouter()

ingresos_db = {}
movimientos_db = {}
ingreso_counter = 0
movimiento_counter = 0


@router.get("/")
async def get_panol_status():
    return {"module": "Pañol", "status": "active"}


@router.post("/ingresos")
async def registrar_ingreso(payload: dict):
    global ingreso_counter
    ingreso_counter += 1
    ingreso = {"id": ingreso_counter, **payload, "estado": "ingresado"}
    ingresos_db[ingreso_counter] = ingreso
    return {"message": "Ingreso registrado en stock", "data": ingreso}


@router.get("/ingresos")
async def list_ingresos():
    return {"data": list(ingresos_db.values())}


@router.post("/movimientos/produccion")
async def despachar_a_produccion(payload: dict):
    global movimiento_counter
    movimiento_counter += 1
    movimiento = {"id": movimiento_counter, **payload, "estado": "despachado"}
    movimientos_db[movimiento_counter] = movimiento
    return {"message": "Material despachado a Producción", "data": movimiento}


@router.get("/movimientos")
async def list_movimientos():
    return {"data": list(movimientos_db.values())}
