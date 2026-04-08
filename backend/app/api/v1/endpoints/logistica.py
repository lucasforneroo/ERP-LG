from fastapi import APIRouter, HTTPException

router = APIRouter()

despachos_db = {}
despacho_counter = 0


@router.get("/")
async def get_logistica_status():
    return {"module": "Logística", "status": "active"}


@router.post("/despachos")
async def create_despacho(payload: dict):
    global despacho_counter
    despacho_counter += 1
    despacho = {"id": despacho_counter, **payload, "estado": "pendiente"}
    despachos_db[despacho_counter] = despacho
    return {"message": "Despacho creado", "data": despacho}


@router.get("/despachos")
async def list_despachos():
    return {"data": list(despachos_db.values())}


@router.post("/despachos/{despacho_id}/solicitar-autorizacion")
async def solicitar_autorizacion(despacho_id: int):
    if despacho_id not in despachos_db:
        raise HTTPException(status_code=404, detail=f"Despacho {despacho_id} no encontrado")
    despachos_db[despacho_id]["estado"] = "esperando_autorizacion"
    return {"message": f"Autorización solicitada para despacho {despacho_id}", "data": despachos_db[despacho_id]}


@router.post("/despachos/{despacho_id}/ejecutar")
async def ejecutar_despacho(despacho_id: int):
    if despacho_id not in despachos_db:
        raise HTTPException(status_code=404, detail=f"Despacho {despacho_id} no encontrado")
    despachos_db[despacho_id]["estado"] = "ejecutado"
    return {"message": f"Despacho {despacho_id} ejecutado", "data": despachos_db[despacho_id]}
