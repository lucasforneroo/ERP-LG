from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_comercial_status():
    return {"module": "Comercial", "status": "active"}

@router.post("/ordenes-fabricacion")
async def create_of(payload: dict):
    # Lógica para crear la OF (Track 1)
    return {"message": "Orden de Fabricación recibida", "data": payload}
