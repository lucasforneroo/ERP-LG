from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_produccion_status():
    return {"module": "Producción", "status": "active"}

@router.post("/lotes-terminados")
async def finalizar_lote(payload: dict):
    # Cierre de producción y transferencia a Logística
    return {"message": "Lote finalizado y transferido a Logística", "data": payload}
