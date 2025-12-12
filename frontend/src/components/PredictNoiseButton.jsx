// frontend/src/components/PredictNoiseButton.jsx
import React, { useState } from "react";

const API_URL = "http://localhost:8070/api/predictions/run";

function PredictNoiseButton() {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [plots, setPlots] = useState(null);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0); // 👈 para romper caché de imágenes

  const handleClick = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
      });

      if (!res.ok) {
        let detail = `Error HTTP ${res.status}`;
        try {
          const data = await res.json();
          if (data?.detail) detail = data.detail;
        } catch (_) {}
        throw new Error(detail);
      }

      const data = await res.json();
      console.log("Predicciones:", data);

      setMetrics(data.metrics || null);
      setPlots(data.plots || null);

      // 👇 Cada vez que llega una nueva predicción, cambiamos la clave
      //    Esto hace que las URLs de las imágenes sean diferentes y el navegador
      //    se vea obligado a pedirlas de nuevo al backend.
      setRefreshKey((prev) => prev + 1);
    } catch (err) {
      console.error("Error al generar predicciones:", err);
      setError(err.message || "Error al generar predicciones");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-4 space-y-4">
      <button
        type="button"
        onClick={handleClick}
        disabled={loading}
        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {loading ? "Generando predicción..." : "Generar predicción de ruido"}
      </button>

      {error && (
        <p className="text-sm text-red-600">
          Error al generar predicciones: {error}
        </p>
      )}

      {metrics && (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h4 className="text-md font-semibold text-gray-800 mb-2">
            Resumen del modelo de predicción
          </h4>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>
              <span className="font-medium">R² (coef. de determinación):</span>{" "}
              {metrics.r2?.toFixed ? metrics.r2.toFixed(4) : metrics.r2}
            </li>
            <li>
              <span className="font-medium">MSE (error cuadrático medio):</span>{" "}
              {metrics.mse?.toFixed ? metrics.mse.toFixed(4) : metrics.mse}
            </li>
            <li>
              <span className="font-medium">
                RMSE (raíz del error cuadrático medio):
              </span>{" "}
              {metrics.rmse?.toFixed ? metrics.rmse.toFixed(4) : metrics.rmse}
            </li>
            <li>
              <span className="font-medium">MAE (error absoluto medio):</span>{" "}
              {metrics.mae?.toFixed ? metrics.mae.toFixed(4) : metrics.mae}
            </li>
            <li className="mt-1 text-gray-600">
              <span className="font-medium">Muestras totales:</span>{" "}
              {metrics.n_total} &nbsp;|&nbsp;
              <span className="font-medium">Train:</span> {metrics.n_train} &nbsp;|&nbsp;
              <span className="font-medium">Test:</span> {metrics.n_test}
            </li>
          </ul>
        </div>
      )}

      {plots && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-2">
          {/* Serie temporal */}
          <div className="bg-white rounded-lg shadow p-3">
            <h5 className="text-sm font-semibold text-gray-800 mb-2">
              Serie temporal: ruido real vs predicho
            </h5>
            <img
              src={`http://localhost:8070${plots.time_series}?t=${refreshKey}`}
              alt="Serie temporal real vs predicho"
              className="w-full h-auto rounded border"
            />
          </div>

          {/* Dispersión */}
          <div className="bg-white rounded-lg shadow p-3">
            <h5 className="text-sm font-semibold text-gray-800 mb-2">
              Dispersión: nivel real vs predicho
            </h5>
            <img
              src={`http://localhost:8070${plots.scatter}?t=${refreshKey}`}
              alt="Dispersión real vs predicho"
              className="w-full h-auto rounded border"
            />
          </div>

          {/* Errores */}
          <div className="bg-white rounded-lg shadow p-3">
            <h5 className="text-sm font-semibold text-gray-800 mb-2">
              Error del modelo a lo largo del tiempo
            </h5>
            <img
              src={`http://localhost:8070${plots.errors}?t=${refreshKey}`}
              alt="Errores en el tiempo"
              className="w-full h-auto rounded border"
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default PredictNoiseButton;
