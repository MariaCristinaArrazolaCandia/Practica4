from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date, timedelta

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

class SoundDailyPoint(BaseModel):
    date: date
    value: float | None

class SoundDailyResponse(BaseModel):
    metric: str                      # laeq, lai o lai_max
    start_date: date
    end_date: date
    dev_eui: Optional[str] = None
    daily_values: List[SoundDailyPoint]
    global_avg: float | None


class SoundPoint(BaseModel):
    time: datetime
    laeq: float | None

class SoundSeries(BaseModel):
    dev_eui: str
    device_name: str
    points: List[SoundPoint]

class SoundSeriesResponse(BaseModel):
    start_date: date
    end_date: date
    series: List[SoundSeries]


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


@router.get("/sound-daily", response_model=SoundDailyResponse)
def get_sound_daily(
    metric: str = Query(
        "laeq",
        description="Métrica a graficar: laeq (nivel de sonido), lai (promedio), lai_max (pico máximo)"
    ),
    start_date: Optional[date] = Query(
        None, description="Fecha de inicio (YYYY-MM-DD). Por defecto: hace 7 días."
    ),
    end_date: Optional[date] = Query(
        None, description="Fecha de fin (YYYY-MM-DD). Por defecto: hoy."
    ),
    dev_eui: Optional[str] = Query(
        None,
        description="Opcional: filtrar por un dispositivo concreto (dev_eui)."
    ),
    # Si quieres protegerlo con token, descomenta esto y añade el parámetro:
    # token: str = Depends(oauth2_scheme),
):
    """
    Devuelve los promedios diarios de ruido para la métrica indicada
    (`laeq`, `lai`, `lai_max`) en el intervalo de fechas, junto con
    el promedio global del mismo rango.

    Esto es lo que necesitas para dibujar:
      - barras por día
      - línea de promedio global
    en el frontend.
    """
    # --- Validar métrica y mapear a columna SQL segura ---
    metric = metric.lower()
    metric_map = {
        "laeq": "sm.laeq",
        "lai": "sm.lai",
        "lai_max": "sm.lai_max",
    }
    if metric not in metric_map:
        raise HTTPException(
            status_code=400,
            detail="Métrica inválida. Usa 'laeq', 'lai' o 'lai_max'.",
        )

    metric_column = metric_map[metric]

    # --- Rango de fechas por defecto (últimos 7 días) ---
    today = date.today()
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(days=6)

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date no puede ser mayor que end_date.",
        )

    # --- Conexión a MySQL ---
    conn = get_mysql_conn()
    if conn is None:
        raise HTTPException(
            status_code=500,
            detail="No se pudo conectar a la base de datos MySQL.",
        )

    try:
        cursor = conn.cursor(dictionary=True)

        # Construir cláusulas WHERE de forma segura
        where_clauses = [
            f"{metric_column} IS NOT NULL",
            "DATE(u.time) BETWEEN %s AND %s",
        ]
        params: list = [start_date, end_date]

        if dev_eui:
            where_clauses.append("u.dev_eui = %s")
            params.append(dev_eui)

        where_sql = " AND ".join(where_clauses)

        # --- Consulta para valores diarios (barras) ---
        sql_daily = f"""
            SELECT
                DATE(u.time) AS date,
                AVG({metric_column}) AS value
            FROM sound_measurements sm
            JOIN uplinks u ON sm.uplink_id = u.id
            WHERE {where_sql}
            GROUP BY DATE(u.time)
            ORDER BY DATE(u.time) ASC
        """
        cursor.execute(sql_daily, params)
        daily_rows = cursor.fetchall()

        if not daily_rows:
            raise HTTPException(
                status_code=404,
                detail="No hay datos de sonido para el rango de fechas indicado.",
            )

        # --- Consulta para promedio global (línea) ---
        sql_global = f"""
            SELECT
                AVG({metric_column}) AS global_avg
            FROM sound_measurements sm
            JOIN uplinks u ON sm.uplink_id = u.id
            WHERE {where_sql}
        """
        cursor.execute(sql_global, params)
        global_row = cursor.fetchone()
        global_avg = global_row["global_avg"] if global_row else None

        # Mapear a modelo Pydantic
        daily_values = [
            SoundDailyPoint(date=row["date"], value=row["value"])
            for row in daily_rows
        ]

        return SoundDailyResponse(
            metric=metric,
            start_date=start_date,
            end_date=end_date,
            dev_eui=dev_eui,
            daily_values=daily_values,
            global_avg=global_avg,
        )
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/sound-series", response_model=SoundSeriesResponse)
def get_sound_series(
    start_date: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    dev_eui: Optional[str] = Query(None, description="Opcional: filtrar por un dispositivo"),
):
    """
    Devuelve series de tiempo de LAeq por dispositivo, para graficar
    múltiples líneas (una por dispositivo) en el frontend.
    """
    today = date.today()
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(days=7)

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date no puede ser mayor que end_date")

    conn = get_mysql_conn()
    if conn is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a MySQL")

    try:
        cursor = conn.cursor(dictionary=True)

        where = ["DATE(u.time) BETWEEN %s AND %s"]
        params: list = [start_date, end_date]

        if dev_eui:
            where.append("u.dev_eui = %s")
            params.append(dev_eui)

        where_sql = " AND ".join(where)

        # Ajusta el nombre de la tabla de dispositivos si en tu esquema se llama distinto
        sql = f"""
            SELECT
                u.dev_eui,
                COALESCE(d.name, u.dev_eui) AS device_name,
                u.time,
                sm.laeq
            FROM sound_measurements sm
            JOIN uplinks u ON sm.uplink_id = u.id
            LEFT JOIN devices d ON d.dev_eui = u.dev_eui
            WHERE {where_sql}
            ORDER BY u.dev_eui, u.time
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No hay datos en el rango indicado")

        # Agrupar por dev_eui
        by_dev: dict[str, dict] = {}
        for row in rows:
            key = row["dev_eui"]
            if key not in by_dev:
                by_dev[key] = {
                    "dev_eui": key,
                    "device_name": row["device_name"],
                    "points": [],
                }
            by_dev[key]["points"].append(
                {
                    "time": row["time"],
                    "laeq": row["laeq"],
                }
            )

        series = [
            SoundSeries(
                dev_eui=dev_key,
                device_name=data["device_name"],
                points=[SoundPoint(**p) for p in data["points"]],
            )
            for dev_key, data in by_dev.items()
        ]

        return SoundSeriesResponse(
            start_date=start_date,
            end_date=end_date,
            series=series,
        )
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
