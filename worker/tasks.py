import os
import csv
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import datetime as dt

from celery import Celery
from kombu import Queue

from db_mysql import get_mysql_conn
from pymongo import MongoClient


# ------------------------------------------------------
# Celery – usar RabbitMQ como broker (NO redis)
# ------------------------------------------------------
BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "amqp://guest:guest@rabbitmq:5672//"  # RabbitMQ en docker-compose
)
BACKEND_URL = os.getenv(
    "CELERY_RESULT_BACKEND",
    "rpc://"  # backend clásico con RabbitMQ
)

celery_app = Celery(
    "worker",
    broker=BROKER_URL,
    backend=BACKEND_URL,
)

celery_app.conf.task_queues = (
    Queue("default", routing_key="default"),
)


# ------------------------------------------------------
# Mongo para logs
# ------------------------------------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "monitoring")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "csv_runs")

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]
runs_collection = mongo_db[MONGO_COLLECTION]


# ------------------------------------------------------
# Utilidades de parseo
# ------------------------------------------------------
def parse_bool(value):
    if value is None or value == "":
        return None
    v = str(value).strip().lower()
    if v in ("true", "1", "yes", "y", "si", "sí"):
        return True
    if v in ("false", "0", "no", "n"):
        return False
    return None


def parse_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except:
        return None


def parse_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except:
        return None


def parse_datetime(value):
    if not value:
        return None
    v = str(value).strip()
    if v.endswith("Z"):
        v = v[:-1]
    v = v.replace("T", " ")
    try:
        return datetime.fromisoformat(v)
    except:
        return None


# ------------------------------------------------------
# Gráfico simple (barras + línea promedio)
# ------------------------------------------------------
def generar_grafico_sonido(
    df: pd.DataFrame,
    metric_col: str,
    start_date: dt.date,
    end_date: dt.date,
    output_dir: str = "/data/charts",
) -> str:
    """
    Genera un gráfico de barras por día con la variable `metric_col`
    y una línea horizontal con el promedio global.
    """
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])

    df["date"] = df["time"].dt.date

    mask = (df["date"] >= start_date) & (df["date"] <= end_date)
    df_range = df.loc[mask]

    daily = df_range.groupby("date")[metric_col].mean().dropna()
    if daily.empty:
        raise ValueError("Sin datos válidos para gráfico")

    mean_val = daily.mean()

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"sonido_{metric_col.replace('.', '_')}_{start_date}_{end_date}.png"
    full_path = os.path.join(output_dir, filename)

    plt.figure(figsize=(10, 5))
    plt.bar(daily.index.astype(str), daily.values, label=f"Promedio diario ({metric_col})")
    plt.axhline(mean_val, linestyle="--", label=f"Promedio global: {mean_val:.2f}")

    plt.xticks(rotation=45)
    plt.xlabel("Fecha")
    plt.ylabel(metric_col)
    plt.title(f"{metric_col} por día ({start_date} a {end_date})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(full_path, dpi=120)
    plt.close()

    return full_path


# ------------------------------------------------------
# GRÁFICO MULTISERIES (una línea por dev_eui)
# ------------------------------------------------------
def generar_grafico_multiseries(
    df: pd.DataFrame,
    start_date: dt.date,
    end_date: dt.date,
    output_dir: str = "/data/charts",
) -> str:
    """
    df contiene: time, dev_eui, laeq
    """
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])
    df = df[df["laeq"].notna()]

    mask = (df["time"].dt.date >= start_date) & (df["time"].dt.date <= end_date)
    df = df.loc[mask]

    if df.empty:
        raise ValueError("Sin datos para gráfico multiseries")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"series_sonido_{start_date}_{end_date}.png"
    full_path = os.path.join(output_dir, filename)

    plt.figure(figsize=(12, 6))

    for dev, df_dev in df.groupby("dev_eui"):
        plt.plot(df_dev["time"], df_dev["laeq"], label=str(dev), marker="o", linewidth=1)

    plt.xlabel("Tiempo")
    plt.ylabel("LAeq")
    plt.title(f"Series de sonido por dispositivo ({start_date} a {end_date})")
    plt.legend(fontsize="small")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(full_path, dpi=150)
    plt.close()

    return full_path


# ------------------------------------------------------
# TAREA PRINCIPAL
# ------------------------------------------------------
@celery_app.task(name="worker.tasks.procesar_csv")
def procesar_csv(path_csv: str) -> dict:
    print(f"[worker] Procesando CSV: {path_csv}")

    if not os.path.exists(path_csv):
        err = {"ok": False, "error": "Archivo no encontrado"}
        _log_run(path_csv, err)
        return err

    conn = get_mysql_conn()
    if conn is None:
        err = {"ok": False, "error": "No se pudo conectar a MySQL"}
        _log_run(path_csv, err)
        return err

    cursor = conn.cursor()

    processed = 0
    errors = 0
    errors_sql = 0
    errors_other = 0
    sound_rows = 0
    skipped_no_dev_eui = 0
    skipped_bad_time = 0
    inserted_uplinks = 0
    updated_uplinks = 0

    # Para construir gráficos
    df_rows = []

    try:
        with open(path_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                processed += 1

                try:
                    dev_eui = row.get("deviceInfo.devEui") or row.get("deviceInfo.devEUI")
                    if not dev_eui:
                        skipped_no_dev_eui += 1
                        continue

                    time_dt = parse_datetime(row.get("time"))
                    if not time_dt:
                        skipped_bad_time += 1
                        continue

                    # INSERT/UPDATE uplinks
                    dedup_id = row.get("context.deduplication_id") or row.get("deduplicationId")

                    f_port = parse_int(row.get("fPort"))
                    f_cnt = parse_int(row.get("fCnt"))
                    adr = parse_bool(row.get("adr"))
                    dr = parse_int(row.get("dr"))
                    confirmed = parse_bool(row.get("confirmed"))
                    margin = parse_int(row.get("margin"))
                    battery_unavailable = parse_bool(row.get("batteryLevelUnavailable"))
                    external_power = parse_bool(row.get("externalPowerSource"))
                    battery_level = parse_float(row.get("batteryLevel"))
                    raw_data = row.get("data")

                    insert_up = """
                        INSERT INTO uplinks (
                            deduplication_id, dev_eui, time,
                            f_port, f_cnt, adr, dr, confirmed,
                            margin, battery_level_unavailable,
                            external_power_source, battery_level,
                            raw_data
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            f_port=VALUES(f_port),
                            f_cnt=VALUES(f_cnt),
                            adr=VALUES(adr),
                            dr=VALUES(dr),
                            confirmed=VALUES(confirmed),
                            margin=VALUES(margin),
                            battery_level_unavailable=VALUES(battery_level_unavailable),
                            external_power_source=VALUES(external_power_source),
                            battery_level=VALUES(battery_level),
                            raw_data=VALUES(raw_data)
                    """

                    cursor.execute(insert_up, (
                        dedup_id, dev_eui, time_dt,
                        f_port, f_cnt, adr, dr, confirmed,
                        margin, battery_unavailable,
                        external_power, battery_level,
                        raw_data,
                    ))

                    if cursor.rowcount == 1:
                        inserted_uplinks += 1
                    else:
                        updated_uplinks += 1

                    # Obtener el uplink_id
                    cursor.execute(
                        "SELECT id FROM uplinks WHERE deduplication_id=%s",
                        (dedup_id,)
                    )
                    row_u = cursor.fetchone()
                    if not row_u:
                        errors_sql += 1
                        continue
                    uplink_id = row_u[0]

                    # SOUND MEASUREMENTS
                    laeq = parse_float(row.get("object.LAeq"))
                    lai = parse_float(row.get("object.LAI"))
                    lai_max = parse_float(row.get("object.LAImax"))
                    obj_batt = parse_float(row.get("object.battery"))
                    status_msg = row.get("object.status")

                    if any(v is not None for v in [laeq, lai, lai_max, obj_batt, status_msg]):
                        cursor.execute(
                            """
                            INSERT INTO sound_measurements (
                                uplink_id, laeq, lai, lai_max, object_battery, status
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                laeq=VALUES(laeq),
                                lai=VALUES(lai),
                                lai_max=VALUES(lai_max),
                                object_battery=VALUES(object_battery),
                                status=VALUES(status)
                            """,
                            (uplink_id, laeq, lai, lai_max, obj_batt, status_msg)
                        )
                        sound_rows += 1

                    # Guardar para pandas (gráficos)
                    df_rows.append({
                        "time": time_dt,
                        "dev_eui": dev_eui,
                        "object.LAeq": laeq,
                        "object.LAI": lai,
                        "object.LAImax": lai_max,
                    })

                except Exception as e:
                    errors += 1
                    try:
                        conn.rollback()
                    except:
                        pass
                    if processed <= 20:
                        print(f"[worker] Error fila {processed}: {e}")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"[worker] ERROR general: {e}")

    finally:
        cursor.close()
        conn.close()

    # ------------------------------------------------------
    # GENERACIÓN DE GRÁFICOS
    # ------------------------------------------------------
    charts = {}
    series_chart = None

    try:
        df = pd.DataFrame(df_rows)
        if not df.empty:
            start_date = df["time"].min().date()
            end_date = df["time"].max().date()

            for col in ["object.LAeq", "object.LAI", "object.LAImax"]:
                try:
                    # Usamos sólo la parte final del nombre (LAeq, LAI, LAImax)
                    # y la pasamos a minúsculas: laeq, lai, laimax
                    key = col.split(".")[-1].lower()
                    charts[key] = generar_grafico_sonido(
                        df, col, start_date, end_date
                    )
                except Exception as e:
                    print(f"[worker] Error gráfico {col}: {e}")

            # MULTISERIES (usa sólo LAeq)
            try:
                df_multi = df[["time", "dev_eui", "object.LAeq"]].rename(columns={"object.LAeq": "laeq"})
                series_chart = generar_grafico_multiseries(df_multi, start_date, end_date)
            except Exception as e:
                print(f"[worker] Error gráfico multiseries: {e}")

    except Exception as e:
        print(f"[worker] Error procesando DataFrame para gráficos: {e}")

    # ------------------------------------------------------
    # STATUS + NOTIFICACIÓN
    # ------------------------------------------------------
    status = {
        "ok": True,
        "processed": processed,
        "inserted_uplinks": inserted_uplinks,
        "updated_uplinks": updated_uplinks,
        "sound_rows": sound_rows,
        "errors": errors,
        "errors_sql": errors_sql,
        "errors_other": errors_other,
        "skipped_no_dev_eui": skipped_no_dev_eui,
        "skipped_bad_time": skipped_bad_time,
        "charts": charts,
        "series_chart": series_chart,
    }

    _log_run(path_csv, status)

    try:
        import requests
        URL = os.getenv("BACKEND_NOTIFY_URL", "http://backend:8070/api/notify/csv-completed")
        requests.post(URL, json=status, timeout=5)
    except Exception as e:
        print(f"[worker] Error notificando al backend: {e}")

    # MOVER ARCHIVO
    try:
        import shutil
        processed_dir = "/data/processed"
        os.makedirs(processed_dir, exist_ok=True)
        shutil.move(path_csv, os.path.join(processed_dir, os.path.basename(path_csv)))
        print(f"[worker] Archivo movido a /data/processed/")
    except Exception as e:
        print(f"[worker] Error moviendo archivo: {e}")

    return status


# ------------------------------------------------------
# Log en Mongo
# ------------------------------------------------------
def _log_run(path_csv: str, status: dict):
    try:
        runs_collection.insert_one({
            "file_name": os.path.basename(path_csv),
            "path": path_csv,
            "run_at": datetime.utcnow(),
            "status": status,
        })
        status["_logged_in_mongo"] = True
    except Exception as e:
        print(f"[worker] No se pudo loguear en Mongo: {e}")
        status["_logged_in_mongo"] = False
