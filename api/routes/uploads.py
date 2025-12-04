# api/routes/uploads.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
import os
from pathlib import Path

from celery import Celery

router = APIRouter()

# Celery client para enviar tareas al worker
celery_app = Celery(
    "api_client",
    broker="amqp://guest:guest@rabbitmq:5672//",
    backend="rpc://",
)

# Nombre de la tarea tal como está definido en worker/tasks.py
# @celery_app.task(name="worker.tasks.procesar_csv")
CELERY_TASK_NAME = "worker.tasks.procesar_csv"

INCOMING_DIR = Path("/data/incoming")


@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)) -> Dict:
    """
    Recibe un archivo CSV desde el frontend, lo guarda en /data/incoming
    (volumen compartido con el worker) y dispara la tarea Celery para
    procesarlo.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .csv")

    try:
        INCOMING_DIR.mkdir(parents=True, exist_ok=True)
        save_path = INCOMING_DIR / file.filename

        # Guardar archivo en disco
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Disparar tarea Celery en el worker, por nombre
        # El worker debe tener @celery_app.task(name="worker.tasks.procesar_csv")
        celery_app.send_task(CELERY_TASK_NAME, args=[str(save_path)])

        return {
            "ok": True,
            "filename": file.filename,
            "saved_path": str(save_path),
            "message": "CSV recibido. El worker está procesando el archivo."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {e}")
