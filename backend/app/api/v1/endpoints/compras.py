from fastapi import APIRouter

router = APIRouter()

facturas_db = {}
factura_counter = 0


@router.get("/")
async def get_compras_status():
    return {"module": "Compras", "status": "active"}


@router.post("/facturas")
async def registrar_factura(payload: dict):
    global factura_counter
    factura_counter += 1
    factura = {"id": factura_counter, **payload, "estado": "registrada"}
    facturas_db[factura_counter] = factura
    return {"message": "Factura registrada", "data": factura}


@router.get("/facturas")
async def list_facturas():
    return {"data": list(facturas_db.values())}
