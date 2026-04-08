from fastapi import APIRouter

router = APIRouter()

lotes_db = {}
lote_counter = 0


@router.get("/")
async def get_produccion_status():
    return {"module": "Producción", "status": "active"}


@router.post("/lotes-terminados")
async def finalizar_lote(payload: dict):
    global lote_counter
    lote_counter += 1
    lote = {"id": lote_counter, **payload, "estado": "terminado"}
    lotes_db[lote_counter] = lote
    return {"message": "Lote finalizado y transferido a Logística", "data": lote}


@router.get("/lotes-terminados")
async def list_lotes():
    return {"data": list(lotes_db.values())}
