from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_compras_status():
    return {"module": "Compras", "status": "active"}

@router.post("/facturas")
async def registrar_factura(payload: dict):
    # Registro de compra y notificación a Pañol
    return {"message": "Factura registrada con éxito", "data": payload}
