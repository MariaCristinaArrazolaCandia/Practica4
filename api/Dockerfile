FROM python:3.11-slim

WORKDIR /app

# Copiar requirements.txt desde ESTA carpeta (api/)
COPY requirements.txt /app/requirements.txt

# Instalar dependencias
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar TODO el código del backend (esta misma carpeta) dentro de /app
COPY . /app

# Comando por defecto
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
