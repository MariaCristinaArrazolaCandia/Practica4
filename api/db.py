import mysql.connector
from mysql.connector import Error
from pymongo import MongoClient

import os
# --- MySQL ---
def get_mysql_conn():
    """
    Devuelve una conexión viva a MySQL dentro de Docker.
    Acordate de cerrar la conexión cuando termines de usarla.
    """
    try:
        conn = mysql.connector.connect(
            host="mysql",            # nombre del servicio docker-compose
            port=3306,               # puerto interno del contenedor mysql
            user="root",
            password="root123",
            database="sensor_monitoring"
        )
        return conn
    except Error as e:
        print("Error conectando a MySQL:", e)
        return None

# --- Mongo ---
# Lee la URI de la variable de entorno. Si no la encuentra, usa la de Docker por defecto.
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")

# Creamos el cliente global una sola vez
mongo_client = MongoClient(MONGO_URI)

# --- Base de datos para la autenticación de usuarios ---
# Apuntamos a la base de datos y colección correctas donde están los usuarios.
auth_db = mongo_client["EMERGENTES_Monitoreo_GAMC"]
mongo_collection = auth_db["users"]

# --- Base de datos para el sistema ETL (si es diferente) ---
etl_db = mongo_client["etl_system"]
uploads_collection = etl_db["uploads"]
