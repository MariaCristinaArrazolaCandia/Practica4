import pymongo
import bcrypt
from pymongo import MongoClient

# --- Detalles de Conexión a MongoDB ---
# Asegúrate de que esta URI de conexión sea la correcta para tu clúster.
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "EMERGENTES_Monitoreo_GAMC"
COLLECTION_NAME = "users"

# --- Lista de usuarios a crear ---
# Se definen los usuarios con contraseñas en texto plano.
# Estas contraseñas serán cifradas antes de guardarlas en la base de datos.
users_to_create = [
    {
        "username": "alcalde_gamc",
        "password": "123456",
        "fullName": "Alcalde/sa GAMC",
        "role": "Ejecutivo",
        "email": "alcalde@etl.com"
    },
    {
        "username": "director_dgeyci",
        "password": "123456",
        "fullName": "Director/a DGEyCI",
        "role": "Ejecutivo",
        "email": "director@etl.com"
    },
    {
        "username": "admin_sistema",
        "password": "123456",
        "fullName": "Administrador de Sistema",
        "role": "Operativo",
        "email": "admin@etl.com"
    },
    {
        "username": "usuario_operativo",
        "password": "123456",
        "fullName": "Usuario Operativo",
        "role": "Operativo",
        "email": "usuario@etl.com"
    }
]

def populate_users():
    """
    Conecta a MongoDB, cifra las contraseñas y puebla la colección de usuarios.
    """
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        # Limpiar la colección para evitar duplicados en ejecuciones posteriores
        collection.delete_many({})
        print(f"Colección '{COLLECTION_NAME}' limpiada.")

        for user in users_to_create:
            # Cifrar la contraseña usando bcrypt
            hashed_password = bcrypt.hashpw(user["password"].encode('utf-8'), bcrypt.gensalt())
            user["password_hash"] = hashed_password.decode('utf-8')  # Guardar como string
            del user["password"]  # Eliminar la contraseña en texto plano

        # Insertar todos los usuarios en la base de datos
        collection.insert_many(users_to_create)
        print(f"{len(users_to_create)} usuarios han sido creados exitosamente en la colección '{COLLECTION_NAME}'.")

    except pymongo.errors.ConnectionFailure as e:
        print(f"Error de conexión a MongoDB: {e}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        if 'client' in locals() and client:
            client.close()

if __name__ == "__main__":
    populate_users()
