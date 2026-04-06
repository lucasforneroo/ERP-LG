from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_administracion_status():
    return {"module": "Administración", "status": "active"}

@router.put("/anticipos/{anticipo_id}/validar")
async def validar_anticipo(anticipo_id: int):
    # Lógica de validación de anticipos (Track 1)
    return {"message": f"Anticipo {anticipo_id} validado correctamente"}
