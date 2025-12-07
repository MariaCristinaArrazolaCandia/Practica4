from tasks import celery_app

# Nota muy importante:
# Cuando el contenedor arranca, en docker-compose tenemos:
#   command: python etl_worker.py
#
# Pero Celery normalmente se lanza con
#   celery -A tasks worker --loglevel=info
#
# Hay 2 opciones:
#   Opción A: cambiamos docker-compose para usar el comando celery
#   Opción B: desde Python lanzamos celery programáticamente
#
# Vamos a usar Opción A (RECOMENDADA).
#
# Así que este archivo puede quedar vacío o con un comentario explicando.
#

if __name__ == "__main__":
    print("El worker Celery no se ejecuta aquí directamente. Se lanza con 'celery -A tasks worker --loglevel=info' en docker-compose.")
