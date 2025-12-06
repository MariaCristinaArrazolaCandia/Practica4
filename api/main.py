from fastapi import FastAPI, Request, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from routes import user, upload, status as status_routes, data, ws, notify, dashboard, uploads, predictions, charts


app = FastAPI(
    title="API de Monitoreo GAMC",
    description="API para la gestión de usuarios y datos del sistema de monitoreo.",
    version="1.0.0",
)

# ------------------------------------------------------
# CORS – PERMISIVO PARA DESARROLLO
# ------------------------------------------------------
# Mientras estamos desarrollando, lo más sencillo es permitir todo.
# Luego se puede cerrar a dominios concretos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # ⬅️ Permite cualquier origen (localhost:3000 incluido)
    allow_credentials=True,
    allow_methods=["*"],          # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],          # Cualquier header (Authorization, Content-Type, etc.)
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"Error no controlado: {exc}")
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Ha ocurrido un error interno en el servidor: {exc}"},
    )


@app.get("/")
def root():
    return {"status": "ok", "message": "Backend Monitoreo GAMC funcionando"}

app.mount("/static", StaticFiles(directory="static"), name="static")
# Servir las imágenes generadas por el worker
app.mount("/charts", StaticFiles(directory="/data/charts"), name="charts")


# Incluir routers con prefijo /api
app.include_router(user.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(status_routes.router, prefix="/api")
app.include_router(data.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(predictions.router, prefix="/api", tags=["predictions"])
app.include_router(charts.router, prefix="/api", tags=["charts"]) 

# WebSocket (sin /api)
app.include_router(ws.router)

# Notificación desde el worker
app.include_router(notify.router, prefix="/api")

# Upload CSV con Celery
app.include_router(uploads.router, prefix="/api", tags=["uploads"])
