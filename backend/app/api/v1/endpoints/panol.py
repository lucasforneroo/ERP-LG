from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_panol_status():
    return {"module": "Pañol", "status": "active"}

@router.post("/ingresos")
async def registrar_ingreso(payload: dict):
    # Ingreso físico de materiales al stock
    return {"message": "Ingreso de material registrado en stock", "data": payload}
