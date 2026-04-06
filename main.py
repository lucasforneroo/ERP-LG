from fastapi import FastAPI

app = FastAPI(title="ERP Industrial API - Track 2")

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Servidor de desarrollo ERP Industrial levantado con éxito",
        "hot_reload": "activado"
    }
