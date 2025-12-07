from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime

from db import get_mysql_conn
from routes.user import oauth2_scheme # Importamos el esquema de seguridad

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)

# --- Modelos de Respuesta ---

class DashboardStats(BaseModel):
    total_devices: int
    avg_laeq_24h: float | None
    low_battery_devices: int
    avg_battery_level: float | None

class NoiseTrendPoint(BaseModel):
    date: str
    avg_noise: float | None

class LatestUplink(BaseModel):
    device_name: str | None
    time: datetime
    battery_level: float | None
    laeq: float | None


# --- Endpoints ---

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats():
    """
    Obtiene estadísticas generales para el dashboard.
    - **total_devices**: Número total de dispositivos registrados.
    - **avg_laeq_24h**: Promedio de ruido (LAeq) en las últimas 24 horas.
    - **low_battery_devices**: Cantidad de dispositivos con batería baja (<20%) en la última semana.
    """
    conn = get_mysql_conn()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos MySQL.")
    
    try:
        cursor = conn.cursor(dictionary=True)

        # Total de dispositivos
        cursor.execute("SELECT COUNT(*) as total FROM devices")
        total_devices = cursor.fetchone()['total']

        # Promedio de ruido (LAeq) en las últimas 24 horas
        cursor.execute("""
            SELECT AVG(sm.laeq) as avg_laeq
            FROM sound_measurements sm
            JOIN uplinks u ON sm.uplink_id = u.id
            WHERE u.time >= NOW() - INTERVAL 24 HOUR
        """)
        avg_laeq_24h = cursor.fetchone()['avg_laeq']

        # Dispositivos con batería baja en la última semana
        cursor.execute("""
            SELECT COUNT(DISTINCT dev_eui) as low_battery_count
            FROM uplinks
            WHERE battery_level IS NOT NULL AND battery_level < 20 AND time >= NOW() - INTERVAL 7 DAY
        """)
        low_battery_devices = cursor.fetchone()['low_battery_count']

         # Promedio del nivel de batería en las últimas 24 horas
        cursor.execute("""
            SELECT AVG(battery_level) as avg_battery
            FROM uplinks
            WHERE battery_level IS NOT NULL AND time >= NOW() - INTERVAL 24 HOUR
        """)
        avg_battery_level = cursor.fetchone()['avg_battery']


        return {
            "total_devices": total_devices,
            "avg_laeq_24h": round(avg_laeq_24h, 2) if avg_laeq_24h else None,
            "low_battery_devices": low_battery_devices,
            "avg_battery_level": round(avg_battery_level, 2) if avg_battery_level else None,
        }
    finally:
        if conn.is_connected():


            cursor.close()
            conn.close()

@router.get("/noise-trend", response_model=List[NoiseTrendPoint])
def get_noise_trend():
    """
    Obtiene la tendencia del nivel de ruido promedio de los últimos 7 días.
    """
    conn = get_mysql_conn()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos MySQL.")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT DATE_FORMAT(u.time, '%Y-%m-%d') as date, AVG(sm.laeq) as avg_noise
            FROM sound_measurements sm
            JOIN uplinks u ON sm.uplink_id = u.id
            WHERE u.time >= NOW() - INTERVAL 7 DAY
            GROUP BY date
            ORDER BY date ASC
        """)
        return cursor.fetchall()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@router.get("/latest-uplinks", response_model=List[LatestUplink])
def get_latest_uplinks():
    """
    Obtiene los 10 últimos reportes (uplinks) de los dispositivos.
    """
    conn = get_mysql_conn()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos MySQL.")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.device_name, u.time, u.battery_level, sm.laeq
            FROM uplinks u
            JOIN devices d ON u.dev_eui = d.dev_eui
            LEFT JOIN sound_measurements sm ON u.id = sm.uplink_id
            ORDER BY u.time DESC
            LIMIT 10
        """)
        return cursor.fetchall()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()