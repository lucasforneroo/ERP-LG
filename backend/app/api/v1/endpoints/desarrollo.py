from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_desarrollo_status():
    return {"module": "Desarrollo", "status": "active"}

@router.post("/pedidos-material")
async def create_pedido_material(payload: dict):
    # Generación de listado de materiales (BOM)
    return {"message": "Pedido de materiales generado", "data": payload}
