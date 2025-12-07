from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime

from db import get_mysql_conn
from routes.user import oauth2_scheme # Importamos el esquema de seguridad para proteger las rutas

router = APIRouter(
    prefix="/data",
    tags=["data"],
)

# --- Modelos Pydantic para las respuestas ---
# Estos modelos ayudan a FastAPI a validar y documentar la salida de la API.

class Device(BaseModel):
    id: int
    dev_eui: str
    device_name: str | None = None
    description: str | None = None
    location_lat: float | None = None
    location_lon: float | None = None
    created_at: datetime | None = None

class Uplink(BaseModel):
    id: int
    dev_eui: str
    time: datetime
    f_port: int | None = None
    f_cnt: int | None = None
    battery_level: float | None = None
    raw_data: str | None = None

class Measurement(BaseModel):
    id: int
    dev_eui: str
    time: datetime

class SoundMeasurement(BaseModel):
    id: int
    uplink_id: int
    laeq: float | None = None
    lai: float | None = None
    lai_max: float | None = None
    object_battery: float | None = None

class DistanceMeasurement(BaseModel):
    id: int
    measurement_id: int
    distance: float | None = None
    position: str | None = None
    battery: float | None = None
    sensor_type: str | None = None


def execute_query(query: str):
    """Función de ayuda para ejecutar consultas y manejar la conexión."""
    conn = get_mysql_conn()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos MySQL.")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/devices", response_model=List[Device])
def get_all_devices(skip: int = 0, limit: int = 100):
    """
    Obtiene una lista paginada de todos los dispositivos.
    """
    query = f"SELECT id, dev_eui, device_name, description, location_lat, location_lon, created_at FROM devices ORDER BY id LIMIT {limit} OFFSET {skip}"
    devices = execute_query(query)
    return devices

@router.get("/devices/{dev_eui}", response_model=Device)
def get_device_by_eui(dev_eui: str):
    """
    Obtiene un dispositivo específico por su `dev_eui`.
    """
    # Usamos execute_query pero con una consulta parametrizada para seguridad
    conn = get_mysql_conn()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos MySQL.")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, dev_eui, device_name, description, location_lat, location_lon, created_at FROM devices WHERE dev_eui = %s", (dev_eui,))
        device = cursor.fetchone()
        if not device:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")
        return device
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/uplinks", response_model=List[Uplink])
def get_all_uplinks(skip: int = 0, limit: int = 100):
    """
    Obtiene una lista paginada de todos los uplinks (reportes de dispositivos).
    """
    query = f"SELECT id, dev_eui, time, f_port, f_cnt, battery_level, raw_data FROM uplinks ORDER BY time DESC LIMIT {limit} OFFSET {skip}"
    uplinks = execute_query(query)
    return uplinks


@router.get("/measurements", response_model=List[Measurement])
def get_all_measurements(skip: int = 0, limit: int = 100):
    """
    Obtiene una lista paginada de todas las mediciones genéricas.
    """
    query = f"SELECT id, dev_eui, time FROM measurements ORDER BY time DESC LIMIT {limit} OFFSET {skip}"
    measurements = execute_query(query)
    return measurements


@router.get("/sound_measurements", response_model=List[SoundMeasurement])
def get_all_sound_measurements(skip: int = 0, limit: int = 100):
    """
    Obtiene una lista paginada de todas las mediciones de sonido.
    """
    query = f"SELECT id, uplink_id, laeq, lai, lai_max, object_battery FROM sound_measurements ORDER BY id DESC LIMIT {limit} OFFSET {skip}"
    sound_measurements = execute_query(query)
    return sound_measurements


@router.get("/distance_measurements", response_model=List[DistanceMeasurement])
def get_all_distance_measurements(skip: int = 0, limit: int = 100):
    """
    Obtiene una lista paginada de todas las mediciones de distancia.
    """
    query = f"SELECT id, measurement_id, distance, position, battery, sensor_type FROM distance_measurements ORDER BY id DESC LIMIT {limit} OFFSET {skip}"
    distance_measurements = execute_query(query)
    return distance_measurements