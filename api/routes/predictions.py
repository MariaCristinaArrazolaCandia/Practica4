# api/routes/predictions.py  (dentro del contenedor: /app/routes/predictions.py)

from fastapi import APIRouter, HTTPException
from pathlib import Path
import os
import traceback

import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")  # Backend sin interfaz gráfica para Docker
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# ============================
# CONFIGURACIÓN DEL ROUTER
# ============================
router = APIRouter(
    prefix="/predictions",     # se combinará con prefix="/api" en main.py → /api/predictions/...
    tags=["Predicciones"],
)

# ============================
# RUTAS Y ARCHIVOS
# ============================
BASE_DIR = Path(__file__).resolve().parent.parent  # /app
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static" / "predictions"

# Aseguramos que el directorio de gráficos existe
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Nombre del CSV dentro de api/data
CSV_PATH = DATA_DIR / "WS302-915M_SONIDO_NOV_2024.csv"

# Parámetros del modelo
AGGREGATE_WEEKLY = False   # False: por medición; True: por semana
USE_DATE_RANGE = False
START_DATE = "2024-11-15"
END_DATE = "2024-11-30"
TEST_SIZE = 0.2  # 20% test


@router.post("/run")
def run_noise_predictions():
    """
    Ejecuta el modelo de regresión lineal sobre el CSV de sonido,
    guarda tres gráficos en /static/predictions y devuelve métricas + URLs.
    """
    try:
        # ----------------------------
        # 1) VALIDAR CSV
        # ----------------------------
        if not CSV_PATH.exists():
            raise HTTPException(
                status_code=500,
                detail=f"El archivo CSV no existe en la ruta: {CSV_PATH}"
            )

        # ----------------------------
        # 2) CARGAR Y PREPROCESAR
        # ----------------------------
        df = pd.read_csv(CSV_PATH, low_memory=False)
        if "time" not in df.columns:
            raise HTTPException(
                status_code=500,
                detail=f"La columna 'time' no existe en el CSV. Columnas disponibles: {list(df.columns)}"
            )

        # Convertir 'time' a datetime
        df["time"] = pd.to_datetime(df["time"], utc=True, format="ISO8601", errors="coerce")
        df = df.dropna(subset=["time"])

        # Asegurar columnas numéricas de ruido
        for col in ["object.LAeq", "object.LAI", "object.LAImax"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Nos quedamos con filas que tengan LAeq
        if "object.LAeq" not in df.columns:
            raise HTTPException(
                status_code=500,
                detail=f"La columna 'object.LAeq' no existe en el CSV. Columnas: {list(df.columns)}"
            )

        df = df.dropna(subset=["object.LAeq"])
        df = df.sort_values("time")

        if len(df) < 10:
            raise HTTPException(
                status_code=500,
                detail=f"No hay suficientes filas con datos de ruido. Filas válidas: {len(df)}"
            )

        # Filtrar por rango de fechas si está activado
        if USE_DATE_RANGE:
            df = df[(df["time"] >= START_DATE) & (df["time"] <= END_DATE)]
            if df.empty:
                raise HTTPException(
                    status_code=500,
                    detail=f"No hay datos en el rango de fechas {START_DATE} a {END_DATE}"
                )

        # -----------------------------------
        # 3) FEATURES PARA EL MODELO
        # -----------------------------------
        if AGGREGATE_WEEKLY:
            df_agg = (
                df.set_index("time")
                  .resample("W")
                  .agg({
                      "object.LAeq": "mean",
                      "object.LAI": "mean" if "object.LAI" in df.columns else "mean",
                      "object.LAImax": "mean" if "object.LAImax" in df.columns else "mean",
                  })
                  .dropna()
                  .reset_index()
            )
            df = df_agg.copy()

            df["year"] = df["time"].dt.year
            df["weekofyear"] = df["time"].dt.isocalendar().week.astype(int)

            feature_cols = ["year", "weekofyear"]
            target_col = "object.LAeq"
        else:
            df["hour"] = df["time"].dt.hour
            df["dayofweek"] = df["time"].dt.dayofweek
            df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)

            feature_cols = ["hour", "dayofweek", "is_weekend"]
            target_col = "object.LAeq"

        X = df[feature_cols]
        y = df[target_col]

        # -----------------------------------
        # 4) TRAIN / TEST
        # -----------------------------------
        n = len(df)
        split_idx = int(n * (1 - TEST_SIZE))
        if split_idx <= 0 or split_idx >= n:
            raise HTTPException(
                status_code=500,
                detail=f"Split de train/test incorrecto. n={n}, split_idx={split_idx}"
            )

        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # -----------------------------------
        # 5) MODELO
        # -----------------------------------
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        # -----------------------------------
        # 6) MÉTRICAS
        # -----------------------------------
        r2 = r2_score(y_test, y_pred) if len(y_test) > 1 else float("nan")
        mse = mean_squared_error(y_test, y_pred)
        rmse = float(np.sqrt(mse))
        mae = mean_absolute_error(y_test, y_pred)

        # -----------------------------------
        # 7) DATAFRAME DE TEST
        # -----------------------------------
        df_test = df.iloc[split_idx:].copy().reset_index(drop=True)
        df_test["LAeq_real"] = y_test.values
        df_test["LAeq_pred"] = y_pred
        df_test["error"] = df_test["LAeq_real"] - df_test["LAeq_pred"]

        # -----------------------------------
        # 8) GRÁFICOS (GUARDAR A PNG)
        # -----------------------------------
        # 8.1 Serie temporal
        plt.figure(figsize=(14, 5))
        plt.plot(df_test["time"], df_test["LAeq_real"], label="Real (LAeq)")
        plt.plot(df_test["time"], df_test["LAeq_pred"], linestyle="--", label="Predicho (LAeq)")
        titulo_tiempo = "Real vs Predicho - Serie temporal"
        if AGGREGATE_WEEKLY:
            titulo_tiempo += " (agrupado por semana)"
        else:
            titulo_tiempo += " (por medición)"
        plt.title(titulo_tiempo)
        plt.xlabel("Tiempo")
        plt.ylabel("Nivel de ruido LAeq")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        serie_path = STATIC_DIR / "serie_tiempo.png"
        plt.savefig(serie_path, bbox_inches="tight")
        plt.close()

        # 8.2 Dispersión
        plt.figure(figsize=(6, 6))
        plt.scatter(df_test["LAeq_real"], df_test["LAeq_pred"], alpha=0.5)
        min_val = min(df_test["LAeq_real"].min(), df_test["LAeq_pred"].min())
        max_val = max(df_test["LAeq_real"].max(), df_test["LAeq_pred"].max())
        plt.plot([min_val, max_val], [min_val, max_val])
        plt.title(f"Real vs Predicho (R² = {r2:.2f})")
        plt.xlabel("LAeq real")
        plt.ylabel("LAeq predicho")
        plt.grid(True)
        plt.tight_layout()
        dispersion_path = STATIC_DIR / "dispersion.png"
        plt.savefig(dispersion_path, bbox_inches="tight")
        plt.close()

        # 8.3 Errores en el tiempo
        plt.figure(figsize=(14, 4))
        plt.plot(df_test["time"], df_test["error"])
        plt.axhline(0, linestyle="--")
        titulo_error = "Error (real - predicho) en el tiempo"
        if AGGREGATE_WEEKLY:
            titulo_error += " (semana)"
        plt.title(titulo_error)
        plt.xlabel("Tiempo")
        plt.ylabel("Error en LAeq (dB)")
        plt.grid(True)
        plt.tight_layout()
        errores_path = STATIC_DIR / "errores.png"
        plt.savefig(errores_path, bbox_inches="tight")
        plt.close()

        # -----------------------------------
        # 9) RESPUESTA JSON PARA EL FRONTEND
        # -----------------------------------
        return {
            "message": "Predicciones generadas correctamente.",
            "metrics": {
                "r2": r2,
                "mse": mse,
                "rmse": rmse,
                "mae": mae,
                "n_total": int(n),
                "n_train": int(len(X_train)),
                "n_test": int(len(X_test)),
            },
            "plots": {
                "time_series": "/static/predictions/serie_tiempo.png",
                "scatter": "/static/predictions/dispersion.png",
                "errors": "/static/predictions/errores.png",
            },
        }

    except HTTPException:
        # Errores que ya vienen con mensaje claro para el cliente
        raise
    except Exception as e:
        # Log para ver el traceback en docker logs
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado al generar predicciones: {e}"
        )
