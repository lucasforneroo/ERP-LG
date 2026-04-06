from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Importamos todos los routers modulares
from app.api.v1.endpoints import (
    comercial, 
    administracion, 
    desarrollo, 
    compras, 
    panol, 
    produccion, 
    logistica
)

app = FastAPI(
    title="ERP Industrial - API Monolítica",
    description="Backend centralizado para validación de arquitectura (Track 2)",
    version="1.0.0"
)

# Configuración de CORS para el Frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción poner el dominio del front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ERP Industrial API Online", "status": "Ready"}

# Registro de routers por dominio
app.include_router(comercial.router, prefix="/api/v1/comercial", tags=["Comercial"])
app.include_router(administracion.router, prefix="/api/v1/administracion", tags=["Administración"])
app.include_router(desarrollo.router, prefix="/api/v1/desarrollo", tags=["Desarrollo"])
app.include_router(compras.router, prefix="/api/v1/compras", tags=["Compras"])
app.include_router(panol.router, prefix="/api/v1/panol", tags=["Pañol"])
app.include_router(produccion.router, prefix="/api/v1/produccion", tags=["Producción"])
app.include_router(logistica.router, prefix="/api/v1/logistica", tags=["Logística"])
