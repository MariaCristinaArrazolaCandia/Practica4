# worker/tasks.py
import os
import csv
from datetime import datetime

from celery import Celery
from kombu import Queue

from db_mysql import get_mysql_conn
from pymongo import MongoClient

# -------------------------------
# Celery
# -------------------------------
celery_app = Celery(
    "etl_worker",
    broker="amqp://guest:guest@rabbitmq:5672//",
    backend="rpc://"
)

celery_app.conf.task_queues = [Queue("csv_processing")]
celery_app.conf.task_default_queue = "csv_processing"

# -------------------------------
# Mongo: logs del ETL
# -------------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
mongo_client = MongoClient(MONGO_URI)
etl_db = mongo_client["etl_system"]
runs_collection = etl_db["runs"]  # logs de ejecuciones


# -------------------------------
# Funciones auxiliares de parsing
# -------------------------------
def parse_bool(value):
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in ("1", "true", "t", "yes", "y"):
        return True
    if v in ("0", "false", "f", "no", "n"):
        return False
    return None


def parse_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def parse_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def parse_datetime(value):
    """
    Intenta parsear el campo time que viene en ISO (ej: 2024-11-13T22:10:00.123Z).
    """
    if not value:
        return None
    v = str(value).strip()
    # Quitamos la Z final y cambiamos T por espacio
    if v.endswith("Z"):
        v = v[:-1]
    v = v.replace("T", " ")
    try:
        return datetime.fromisoformat(v)
    except Exception:
        return None


def parse_location(loc_str):
    """
    deviceInfo.tags.Location -> 'lat,lon'
    """
    if not loc_str:
        return None, None
    try:
        parts = [p.strip() for p in str(loc_str).split(",")]
        if len(parts) != 2:
            return None, None
        lat = float(parts[0])
        lon = float(parts[1])
        return lat, lon
    except Exception:
        return None, None


# -------------------------------
# Tarea principal
# -------------------------------
@celery_app.task(name="worker.tasks.procesar_csv")
def procesar_csv(path_csv: str) -> dict:
    """
    Procesa un CSV con los campos:
    _id, devAddr, deduplicationId, time, deviceInfo.*, fPort, data,
    fCnt, confirmed, adr, dr, margin, batteryLevel*,
    object.LAeq, object.LAI, object.LAImax, object.battery, object.status, context.deduplication_id, etc.

    - Inserta/actualiza devices.
    - Inserta/actualiza uplinks (idempotencia por deduplication_id).
    - Inserta/actualiza sound_measurements.
    - Loguea el resumen en Mongo.
    """
    print(f"[worker] Iniciando procesamiento de CSV: {path_csv}")

    if not os.path.exists(path_csv):
        msg = f"Archivo no encontrado: {path_csv}"
        print(f"[worker] {msg}")
        status = {"ok": False, "error": msg}
        _log_run(path_csv, status)
        return status

    conn = get_mysql_conn()
    if conn is None:
        msg = "No se pudo conectar a MySQL"
        print(f"[worker] {msg}")
        status = {"ok": False, "error": msg}
        _log_run(path_csv, status)
        return status

    cursor = conn.cursor()

    # Mapa en memoria para recuperar devEui a partir de devAddr
    devaddr_to_deveui = {}

    processed = 0
    errors = 0            # Errores reales (excepciones)
    errors_sql = 0
    errors_other = 0

    skipped_no_dev_eui = 0
    skipped_bad_time = 0

    inserted_devices = 0
    updated_devices = 0
    inserted_uplinks = 0
    updated_uplinks = 0
    sound_rows = 0



    try:
        with open(path_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                processed += 1
                try:
                    # ------------------------------------------------
                    # FILTRO 1: tiene que haber devEui
                    # ------------------------------------------------
                    # ---------------------------
                    # Recuperar devEui lo mejor posible
                    # ---------------------------
                    raw_dev_eui = row.get("deviceInfo.devEui") or row.get("deviceInfo.devEUI")
                    dev_addr = row.get("devAddr")

                    # Si en esta fila tenemos devEui y devAddr, alimentamos el mapa
                    if raw_dev_eui and dev_addr:
                        devaddr_to_deveui[dev_addr] = raw_dev_eui

                    dev_eui = raw_dev_eui

                    # Si no tenemos devEui, intentamos recuperarlo usando devAddr
                    if not dev_eui and dev_addr:
                        dev_eui = devaddr_to_deveui.get(dev_addr)

                    # Si aun así no hay devEui, la fila no es útil
                    if not dev_eui:
                        skipped_no_dev_eui += 1
                        # OJO: ya no la contamos como "error", solo como "omitida"
                        continue


                    # ------------------------------------------------
                    # FILTRO 2: tiene que haber time válido
                    # ------------------------------------------------
                    time_str = row.get("time")
                    time_dt = parse_datetime(time_str)
                    if time_dt is None:
                        skipped_bad_time += 1
                        # fila no usable, pero no es "error de sistema"
                        continue

                    # ------------------------------------------------
                    # A partir de aquí ya sabemos que es un uplink útil:
                    #   - dev_eui válido
                    #   - time válido
                    # el resto lo procesamos igual que antes
                    # ------------------------------------------------

                    device_name = row.get("deviceInfo.deviceName")
                    application_name = row.get("deviceInfo.applicationName")
                    tenant_name = row.get("deviceInfo.tenantName")
                    device_profile_name = row.get("deviceInfo.deviceProfileName")
                    description = row.get("deviceInfo.tags.Description")
                    address = row.get("deviceInfo.tags.Address")
                    loc_str = row.get("deviceInfo.tags.Location")
                    lat, lon = parse_location(loc_str)

                    if lat is not None and lon is not None:
                        insert_device_sql = """
                            INSERT INTO devices (
                                dev_eui, device_name, application_name, tenant_name,
                                device_profile_name, description, address,
                                location_lat, location_lon
                            )
                            VALUES (%(dev_eui)s, %(device_name)s, %(application_name)s,
                                    %(tenant_name)s, %(device_profile_name)s,
                                    %(description)s, %(address)s,
                                    %(location_lat)s, %(location_lon)s)
                            ON DUPLICATE KEY UPDATE
                                device_name       = VALUES(device_name),
                                application_name  = VALUES(application_name),
                                tenant_name       = VALUES(tenant_name),
                                device_profile_name = VALUES(device_profile_name),
                                description       = VALUES(description),
                                address           = VALUES(address),
                                location_lat      = VALUES(location_lat),
                                location_lon      = VALUES(location_lon)
                        """
                    else:
                        insert_device_sql = """
                            INSERT INTO devices (
                                dev_eui, device_name, application_name, tenant_name,
                                device_profile_name, description, address
                            )
                            VALUES (%(dev_eui)s, %(device_name)s, %(application_name)s,
                                    %(tenant_name)s, %(device_profile_name)s,
                                    %(description)s, %(address)s)
                            ON DUPLICATE KEY UPDATE
                                device_name       = VALUES(device_name),
                                application_name  = VALUES(application_name),
                                tenant_name       = VALUES(tenant_name),
                                device_profile_name = VALUES(device_profile_name),
                                description       = VALUES(description),
                                address           = VALUES(address)
                        """

                    params_device = {
                        "dev_eui": dev_eui,
                        "device_name": device_name,
                        "application_name": application_name,
                        "tenant_name": tenant_name,
                        "device_profile_name": device_profile_name,
                        "description": description,
                        "address": address,
                        "location_lat": lat,
                        "location_lon": lon,
                    }

                    cursor.execute(insert_device_sql, params_device)
                    if cursor.rowcount == 1:
                        inserted_devices += 1
                    else:
                        updated_devices += 1

                    # ---------------------------
                    # 2) Uplink (medición general)
                    # ---------------------------
                    deduplication_id = (
                        row.get("context.deduplication_id")
                        or row.get("deduplicationId")
                    )

                    f_port = parse_int(row.get("fPort"))
                    f_cnt = parse_int(row.get("fCnt"))
                    adr = parse_bool(row.get("adr"))
                    dr = parse_int(row.get("dr"))
                    confirmed = parse_bool(row.get("confirmed"))
                    margin = parse_int(row.get("margin"))
                    battery_level_unavailable = parse_bool(row.get("batteryLevelUnavailable"))
                    external_power_source = parse_bool(row.get("externalPowerSource"))
                    battery_level = parse_float(row.get("batteryLevel"))
                    raw_data = row.get("data")

                    insert_uplink_sql = """
                        INSERT INTO uplinks (
                            deduplication_id, dev_eui, time,
                            f_port, f_cnt, adr, dr, confirmed,
                            margin, battery_level_unavailable,
                            external_power_source, battery_level,
                            raw_data
                        )
                        VALUES (
                            %(deduplication_id)s, %(dev_eui)s, %(time)s,
                            %(f_port)s, %(f_cnt)s, %(adr)s, %(dr)s, %(confirmed)s,
                            %(margin)s, %(battery_level_unavailable)s,
                            %(external_power_source)s, %(battery_level)s,
                            %(raw_data)s
                        )
                        ON DUPLICATE KEY UPDATE
                            f_port = VALUES(f_port),
                            f_cnt  = VALUES(f_cnt),
                            adr    = VALUES(adr),
                            dr     = VALUES(dr),
                            confirmed = VALUES(confirmed),
                            margin    = VALUES(margin),
                            battery_level_unavailable = VALUES(battery_level_unavailable),
                            external_power_source     = VALUES(external_power_source),
                            battery_level             = VALUES(battery_level),
                            raw_data                  = VALUES(raw_data)
                    """

                    params_uplink = {
                        "deduplication_id": deduplication_id,
                        "dev_eui": dev_eui,
                        "time": time_dt,
                        "f_port": f_port,
                        "f_cnt": f_cnt,
                        "adr": adr,
                        "dr": dr,
                        "confirmed": confirmed,
                        "margin": margin,
                        "battery_level_unavailable": battery_level_unavailable,
                        "external_power_source": external_power_source,
                        "battery_level": battery_level,
                        "raw_data": raw_data,
                    }

                    cursor.execute(insert_uplink_sql, params_uplink)
                    if cursor.rowcount == 1:
                        inserted_uplinks += 1
                    else:
                        updated_uplinks += 1

                    # Obtener uplink_id
                    if deduplication_id:
                        cursor.execute(
                            "SELECT id FROM uplinks WHERE deduplication_id = %s",
                            (deduplication_id,),
                        )
                        row_u = cursor.fetchone()
                    else:
                        cursor.execute(
                            """
                            SELECT id FROM uplinks
                            WHERE dev_eui = %s AND time = %s
                                  AND (f_cnt = %s OR (%s IS NULL AND f_cnt IS NULL))
                            ORDER BY id DESC LIMIT 1
                            """,
                            (dev_eui, time_dt, f_cnt, f_cnt),
                        )
                        row_u = cursor.fetchone()

                    if not row_u:
                        errors += 1
                        continue

                    uplink_id = row_u[0]

                    # ---------------------------
                    # 3) Sound measurements
                    # ---------------------------
                    laeq = parse_float(row.get("object.LAeq"))
                    lai = parse_float(row.get("object.LAI"))
                    lai_max = parse_float(row.get("object.LAImax"))
                    obj_batt = parse_float(row.get("object.battery"))
                    status = row.get("object.status")

                    if any(v is not None for v in [laeq, lai, lai_max, obj_batt, status]):
                        insert_sound_sql = """
                            INSERT INTO sound_measurements (
                                uplink_id, laeq, lai, lai_max, object_battery, status
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                laeq = VALUES(laeq),
                                lai = VALUES(lai),
                                lai_max = VALUES(lai_max),
                                object_battery = VALUES(object_battery),
                                status = VALUES(status)
                        """
                        cursor.execute(
                            insert_sound_sql,
                            (uplink_id, laeq, lai, lai_max, obj_batt, status),
                        )
                        sound_rows += 1

                except Exception as e:
                    errors += 1
                    # Intentar clasificar si es error SQL o genérico
                    msg = str(e).lower()
                    if "mysql" in msg or "integrity" in msg or "dataerror" in msg or "programmingerror" in msg:
                        errors_sql += 1
                    else:
                        errors_other += 1

                    if processed <= 20:
                        # Para no llenar logs, solo mostramos detalle en las primeras 20 filas con error
                        print(f"[worker] Error procesando fila {processed}: {type(e).__name__}: {e}")

        conn.commit()

        status = {
            "ok": True,
            "processed": processed,
            "inserted_devices": inserted_devices,
            "updated_devices": updated_devices,
            "inserted_uplinks": inserted_uplinks,
            "updated_uplinks": updated_uplinks,
            "sound_rows": sound_rows,
            "errors": errors,  # errores reales
            "errors_sql": errors_sql,
            "errors_other": errors_other,
            "skipped_no_dev_eui": skipped_no_dev_eui,
            "skipped_bad_time": skipped_bad_time,
        }
        print(f"[worker] CSV procesado OK: {status}")

    except Exception as e:
        conn.rollback()
        status = {
            "ok": False,
            "error": str(e),
            "processed": processed,
            "inserted_devices": inserted_devices,
            "updated_devices": updated_devices,
            "inserted_uplinks": inserted_uplinks,
            "updated_uplinks": updated_uplinks,
            "sound_rows": sound_rows,
            "errors": errors,
        }
        print(f"[worker] Error general procesando CSV {path_csv}: {e}")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    _log_run(path_csv, status)
    try:
        import requests

        BACKEND_NOTIFY_URL = os.getenv(
            "BACKEND_NOTIFY_URL", 
            "http://backend:8070/api/notify/csv-completed"
            )
        # Desde el worker, usamos el nombre del servicio Docker "backend"
        requests.post(BACKEND_NOTIFY_URL, json=status, timeout=5)
    except Exception as e:
        print(f"[worker] No se pudo notificar al backend por HTTP: {e}")

# -----------------------------
# Mover CSV a carpeta processed
# -----------------------------
    try:
        import shutil

        processed_dir = "/data/processed"
        os.makedirs(processed_dir, exist_ok=True)

        file_name = os.path.basename(path_csv)
        new_path = os.path.join(processed_dir, file_name)

        if status.get("ok") is True:
            shutil.move(path_csv, new_path)
            print(f"[worker] Archivo procesado y movido a: {new_path}")
        else:
            print("[worker] Procesamiento fallido: archivo NO movido.")
    except Exception as e:
        print(f"[worker] Error al mover archivo a /data/processed/: {e}")

    return status


def _log_run(path_csv: str, status: dict):
    """
    Registra en MongoDB el resumen de la ejecución.
    """
    try:
        doc = {
            "path": path_csv,
            "file_name": os.path.basename(path_csv),
            "run_at": datetime.utcnow(),
            "status": status,
        }
        runs_collection.insert_one(doc)
        status["_logged_in_mongo"] = True
    except Exception as e:
        print(f"[worker] No se pudo registrar resumen en Mongo: {e}")
        status["_logged_in_mongo"] = False
        status["_mongo_log_error"] = str(e)
