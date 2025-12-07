from fastapi import APIRouter
from datetime import datetime
from routes.ws import manager

router = APIRouter(tags=["notify"])


@router.post("/notify/csv-completed")
async def notify_csv_completed(summary: dict):
    """
    Notificación cuando un CSV termina de procesarse.
    'summary' es el diccionario que envía el worker.
    """
    processed = summary.get("processed", 0)
    errors = summary.get("errors", 0)
    valid_rows = max(processed - errors, 0)

    event = {
        "type": "CSV_COMPLETED",
        "source": "worker",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "processed": processed,
            "valid_rows": valid_rows,
            "inserted_devices": summary.get("inserted_devices", 0),
            "updated_devices": summary.get("updated_devices", 0),
            "inserted_uplinks": summary.get("inserted_uplinks", 0),
            "updated_uplinks": summary.get("updated_uplinks", 0),
            "sound_rows": summary.get("sound_rows", 0),
            "errors": errors,
            "errors_no_dev_eui": summary.get("errors_no_dev_eui", 0),
            "errors_bad_time": summary.get("errors_bad_time", 0),
            "errors_sql": summary.get("errors_sql", 0),
            "errors_other": summary.get("errors_other", 0),
        },
        # Texto listo para mostrar en un toast
        "text": (
            f"CSV procesado: {valid_rows} filas válidas, "
            f"{summary.get('inserted_uplinks', 0)} uplinks, "
            f"{summary.get('sound_rows', 0)} sonidos."
        ),
    }

    await manager.broadcast(event)
    return {"ok": True}
