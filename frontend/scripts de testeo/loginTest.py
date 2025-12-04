import pymongo
import bcrypt
from pymongo import MongoClient
import getpass  # Para ocultar la contraseña al escribirla

# --- Detalles de Conexión a MongoDB ---
# Los mismos detalles que en dataPopulator.py
MONGO_URI = "mongodb+srv://mariaarrazolacom:bvwBTVTrjHX3N22V@client-server.jie5l.mongodb.net/"
DATABASE_NAME = "EMERGENTES_Monitoreo_GAMC"
COLLECTION_NAME = "users"

def simulate_login():
    """
    Simula un proceso de inicio de sesión pidiendo email y contraseña al usuario
    y verificando las credenciales contra la base de datos MongoDB.
    """
    email_input = input("Ingrese su correo electrónico: ")
    # getpass oculta la entrada del teclado para la contraseña
    password_input = getpass.getpass("Ingrese su contraseña: ")

    client = None  # Inicializar cliente a None
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        # 1. Buscar al usuario por su correo electrónico
        user_data = collection.find_one({"email": email_input})

        if user_data:
            # 2. Si el usuario existe, verificar la contraseña
            stored_hash = user_data["password_hash"].encode('utf-8')
            
            if bcrypt.checkpw(password_input.encode('utf-8'), stored_hash):
                print("\n¡Inicio de sesión exitoso!")
                print(f"Bienvenido/a, {user_data['fullName']} ({user_data['role']}).")
            else:
                print("\nError: Contraseña incorrecta.")
        else:
            print("\nError: No se encontró ningún usuario con ese correo electrónico.")

    except pymongo.errors.ConnectionFailure as e:
        print(f"Error de conexión a MongoDB: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    simulate_login()