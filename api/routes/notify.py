from fastapi import APIRouter
from typing import Any, Dict
import os

from routes.ws import manager


router = APIRouter()


def _chart_url(path: str | None) -> str | None:
    """
    Convierte una ruta interna tipo /data/charts/archivo.png
    en una URL estática tipo /charts/archivo.png
    """
    if not path:
        return None
    filename = os.path.basename(path)
    return f"/charts/{filename}"


@router.post("/notify/csv-completed")
async def csv_completed(payload: Dict[str, Any]):
    """
    Recibe el 'status' del worker (procesar_csv) y lo reenvía
    por WebSocket, adaptando las rutas de los gráficos a URLs.
    """
    summary = payload or {}

    charts = summary.get("charts") or {}
    series_chart_path = summary.get("series_chart")

    charts_urls = {
        "laeq": _chart_url(charts.get("laeq")),
        "lai": _chart_url(charts.get("lai")),
        "laimax": _chart_url(charts.get("laimax")),
    }
    series_chart_url = _chart_url(series_chart_path)

    event = {
        "type": "csv_completed",
        "summary": {
            **summary,
            "charts": charts_urls,
            "series_chart": series_chart_url,
        },
        "text": "Procesamiento de CSV completado y gráficos generados.",
    }

    # Enviar por WebSocket
    await manager.broadcast(event)
    # Devolver también por HTTP
    return event
