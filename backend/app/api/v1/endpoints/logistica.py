from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_logistica_status():
    return {"module": "Logística", "status": "active"}

@router.post("/despachos/{despacho_id}/ejecutar")
async def ejecutar_despacho(despacho_id: int):
    # Registro de salida física del equipo
    return {"message": f"Despacho {despacho_id} ejecutado correctamente"}
