# routes/charts.py

from fastapi import APIRouter
from pathlib import Path

router = APIRouter(
    prefix="/charts",
    tags=["charts"],
)

# Carpeta compartida entre backend y worker
CHARTS_DIR = Path("/data/charts")


@router.get("", summary="Lista los gráficos generados a partir de CSV procesados")
def list_charts():
    """
    Devuelve un listado de todos los PNG encontrados en /data/charts,
    con la URL pública para mostrarlos en el frontend.
    """
    if not CHARTS_DIR.exists():
        return {"charts": []}

    charts = []
    # Puedes ajustar el patrón si quieres solo algunos ficheros (ej. '*.png')
    for p in sorted(CHARTS_DIR.glob("*.png")):
        charts.append(
            {
                "filename": p.name,
                # La ruta pública donde se sirven las imágenes
                "url": f"/charts/{p.name}",
            }
        )

    return {"charts": charts}
