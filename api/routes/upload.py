# api/routes/upload.py
import os
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from celery import Celery
from routes.ws import manager  # WebSocket manager para notificaciones

router = APIRouter(tags=["upload"])

celery_app = Celery(
    "backend_producer",
    broker="amqp://guest:guest@rabbitmq:5672//",
    backend="rpc://"
)

UPLOAD_DIR = "/data/inbound"


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Sube un CSV al directorio compartido /data/inbound y encola
    la tarea Celery para procesarlo.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos CSV")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file.filename.replace(' ', '_')}"
    full_path = os.path.join(UPLOAD_DIR, safe_name)

    content = await file.read()
    with open(full_path, "wb") as f:
        f.write(content)

    # Enviar tarea al worker
    task = celery_app.send_task(
        "worker.tasks.procesar_csv",
        args=[full_path],
        queue="csv_processing"
    )

    # Notificar por WebSocket (opcional)
    try:
        await manager.broadcast(f"Nuevo CSV cargado: {file.filename}")
    except Exception:
        # No queremos que falle el upload por un problema en WS
        pass

    return JSONResponse({
        "message": "Archivo recibido y tarea enviada al worker.",
        "saved_as": safe_name,
        "path": full_path,
        "task_id": task.id
    })

