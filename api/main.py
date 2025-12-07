from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, status
from fastapi.responses import JSONResponse
from routes import user, upload, status as status_router, data, ws, notify, dashboard

app = FastAPI(
    title="API de Monitoreo GAMC",
    description="API para la gestión de usuarios y datos del sistema de monitoreo.",
    version="1.0.0"
)


# Orígenes permitidos para CORS. En producción, deberías ser más restrictivo.
origins = [
    "http://localhost:3000",  # El origen de tu frontend de React
    "http://127.0.0.1:3000",
]



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # TEMPORALMENTE: Permite cualquier origen para depuración. ¡Restringir en producción!
    allow_credentials=True,
    allow_methods=["*"],          # permite GET, POST, PUT, etc.
    allow_headers=["*"],          # permite cualquier header (Content-Type, Authorization, etc.)
)

# =================================================================
# MANEJADOR DE EXCEPCIONES GLOBAL
# Esto captura cualquier error no controlado y devuelve una respuesta
# JSON formateada, lo que evita que el error de CORS aparezca en el frontend.
# =================================================================
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Imprime el error en la consola del backend para depuración
    print(f"Error no controlado: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Ha ocurrido un error interno en el servidor: {exc}"},
    )
@app.get("/")
def root():
    return {"status": "ok", "message": "Backend Monitoreo GAMC funcionando"}


# Incluir el router de usuarios con el prefijo /api
# Esto hará que la ruta /users/login esté disponible en /api/users/login
app.include_router(user.router, prefix="/api")
# Montar el router donde está /upload
app.include_router(upload.router, prefix="/api")
# Nuevo endpoint de status
app.include_router(status_router.router, prefix="/api") # Usamos el nombre renombrado
# Nuevo endpoint para consultar datos brutos
app.include_router(data.router, prefix="/api")
# Nuevo endpoint para dashboards
app.include_router(dashboard.router, prefix="/api")


# Rutas WebSocket (sin /api, van directo desde la raíz)
app.include_router(ws.router)

app.include_router(notify.router)
