# Practica3

# Sistema de Monitoreo – Backend, Worker y Dashboard

Este proyecto implementa un **sistema de monitoreo**, compuesto por:

* **API Backend (FastAPI)** – Gestión de usuarios, carga de archivos CSV, consulta de datos y notificaciones en tiempo real.
* **Worker ETL (Celery + Pandas)** – Procesa los CSV provenientes de dispositivos IoT, genera métricas, inserta registros a bases de datos y produce gráficos automatizados.
* **Frontend en React** – Dashboard ejecutivo y operativo, con visualización de métricas, usuarios, notificaciones y gráficos generados por el worker.
* **Base de datos MySQL y MongoDB** – MySQL para almacenamiento estructurado y MongoDB para logs ETL.
* **RabbitMQ** – Broker de mensajería para orquestar tareas ETL.
* **Docker Compose** – Orquestación completa del sistema.

Este documento describe la instalación, configuración, ejecución y estructura del proyecto.

---

## 🚀 Características principales

### 🔹 Ingesta automática de datos (CSV)

Los archivos generados por los dispositivos IoT se cargan mediante la API. Estos son procesados por el worker, generando:

* Parseo y normalización de datos
* Inserción en MySQL (uplinks, dispositivos, mediciones de sonido)
* Registro de la ejecución ETL en MongoDB
* Generación automática de gráficos (PNG)


### 🔹 Dashboard web con React

Permite visualizar:

* Métricas diarias
* Gráficos generados automáticamente
* Uplinks recientes
* Gestión completa de usuarios
* Notificaciones en tiempo real (WebSocket)

### 🔹 Backend sólido con FastAPI

Incluye:

* Gestión JWT de usuarios
* Validación de tokens
* Rutas CRUD de usuarios
* Endpoints de carga de archivos CSV
* Endpoint de monitoreo MySQL / Mongo
* Notificaciones WebSocket
* Exposición de gráficos del worker como archivos estáticos

---

## 🧱 Arquitectura del proyecto

```
project-root/
│
├── api/            # Backend FastAPI
│   ├── main.py
│   ├── routes/
│   ├── db.py
│   ├── ...
│
├── worker/         # ETL con Celery
│   ├── tasks.py
│   ├── transformers.py
│   ├── db_mysql.py
│   ├── ...
│
├── frontend/       # Interfaz React
│   ├── src/
│   ├── public/
│
├── data/
│   ├── inbound/    # CSV cargados
│   ├── charts/     # Gráficos generados por el worker
│
└── docker-compose.yml
```

---

## 🛠️ Instalación del entorno (Windows)

### 1. Instalar herramientas necesarias

Asegúrate de tener instalados:

* **Docker Desktop**
* **Node.js (>=18)**
* **Git**

Verifica:

```bash
docker --version
node -v
npm -v
git --version
```

---

## 🧩 Configuración del proyecto

### 1. Clonar el repositorio

```bash
git clone <https://github.com/MariaCristinaArrazolaCandia/Practica3>
cd project-root
```

### 2. Crear estructura de carpetas

El proyecto requiere estas carpetas (si no existen, Docker las creará):

```
data/inbound
data/charts
```

### 3. Variables de entorno

El archivo `.env` se utiliza principalmente para configurar MongoDB:

```env
# Si deseas usar MongoDB Atlas, descomenta y coloca tu URL
# MONGO_URI=mongodb+srv://.../dbname
```

El sistema usa por defecto:

* `MySQL`: host `mysql`, base `etl_system`
* `Mongo`: host `mongo`, base `etl_system`
* `RabbitMQ`: host `rabbitmq`

Para ambiente local.

Ejecutar el base.sql en mysql que se encuentra en el proyecto 

docker compose exec -T mysql mysql -u root -proot123 < base.sql


de la misma manera ejecutar el dataPopulator.py que se enceuntra dentro d ela carpeta del frontend
esto llenara los datos para el mongoDB

para esto primero tenemos que 

# crear el entorno virtual

python -m venv .venv

# Activar el entorno virtual

.\.venv\Scripts\activate

# Instalar dependencias

pip install pymongo bcrypt

# luego instalar lo necesario en el entorno virtual

pip install --upgrade pip

pip install -r requirements.txt


---

## ▶️ Ejecución del sistema completo

Desde la raíz del proyecto:

```bash
docker compose up -d --build
```

Esto levanta:

* FastAPI (puerto 8070)
* React (puerto 3000)
* Worker Celery
* RabbitMQ
* MySQL
* MongoDB

Puedes verificar los servicios:

```bash
docker compose ps
docker compose logs -f worker
```

---

## 📦 Uso del Frontend (React)

### Instalar dependencias

```bash
cd frontend
npm install
```

### Ejecutar en modo desarrollo

```bash
npm start
```

El dashboard estará en:

```
http://localhost:3000
```

---

## 📂 Backend – API principales (FastAPI)

### 🔸 Subir un CSV

```
POST /api/upload
```

Devuelve un `task_id`.

### 🔸 Ver estado de tarea ETL

```
GET /api/task-status/{task_id}
```

Devuelve:

* contadores del ETL
* ruta del gráfico generado (`/charts/...png`)

### 🔸 Obtener uploads registrados

```
GET /api/mongo/uploads
```

### 🔸 Monitoreo MySQL

```
GET /api/mysql/ping
```

### 🔸 Notificaciones WebSocket

```
ws://localhost:8070/ws/notifications
```

---

## 🔧 Worker – Procesamiento ETL

El worker realiza:

### ✔ Limpieza y normalización del CSV

### ✔ Inserción en MySQL

* `devices`
* `uplinks`
* `sound_measurements`

### ✔ Registro en MongoDB

* Fecha y duración del proceso
* Número de filas procesadas
* Errores y métricas

### ✔ Generación de gráficos automáticos

Los gráficos se guardan aquí:

```
/data/charts/
```

Y son accesibles vía:

```
http://localhost:8070/charts/<archivo>.png
```

---

## 📊 Visualización de gráficos

El frontend puede mostrar gráficos generados por el worker:

```jsx
<img
  src={`http://localhost:8070/charts/${fileName}`}
  alt="Gráfico de sonido"
/>
```

Los nombres de archivo devueltos por el ETL siguen la estructura:

```
sonido_<metric>_<fecha_inicio>_<fecha_fin>.png
```

Ejemplo:

```
sonido_object_LAeq_2024-11-15_2024-11-30.png
```

---

## 🧪 Pruebas

### Probar API

```bash
curl http://localhost:8070/api/mysql/ping
```

### Probar WebSocket

Con cualquier cliente (Insomnia, Postman, WebSocket Debugger):

```
ws://localhost:8070/ws/notifications
```

### Probar carga CSV

Desde frontend: módulo de carga

o usando curl:

```bash
curl -X POST -F "file=@sonido.csv" http://localhost:8070/api/upload
```

---

## 📘 Buenas prácticas adoptadas

* Arquitectura desacoplada API–Worker
* Procesamiento ETL asincrónico
* Archivos compartidos por volúmenes Docker
* Diseño seguro con JWT
* Envío de notificaciones vía WebSocket
* Separación de responsabilidades (API vs Worker vs DB)

---

## 📄 Licencia

Proyecto académico/técnico para prácticas de Tecnologias Emergente I.

---


<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/d3083b99-c739-4640-86dc-57c42db550c0" />



