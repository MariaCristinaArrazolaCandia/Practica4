// frontend/src/components/PredictNoiseButton.jsx

import React, { useState } from "react";

const PREDICTION_API_URL = "http://localhost:8070/api/predictions/run";
const BACKEND_BASE_URL = "http://localhost:8070";

const PredictNoiseButton = () => {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [plots, setPlots] = useState(null);
  const [error, setError] = useState(null);

  const handleRunPrediction = async () => {
    setLoading(true);
    setError(null);
    setMetrics(null);
    setPlots(null);

    try {
      const resp = await fetch(PREDICTION_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || "Error al ejecutar predicciones");
      }

      const data = await resp.json();
      setMetrics(data.metrics || null);
      setPlots(data.plots || null);
    } catch (err) {
      console.error("Error al ejecutar predicciones:", err);
      setError(err.message || "Error desconocido al ejecutar predicciones");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        marginTop: "1rem",
        padding: "1rem",
        borderRadius: "8px",
        border: "1px solid #ccc",
        backgroundColor: "#111827",
        color: "#e5e7eb",
      }}
    >
      <h3 style={{ marginBottom: "0.5rem" }}>
        Predicción de niveles de ruido (LAeq)
      </h3>

      <button
        onClick={handleRunPrediction}
        disabled={loading}
        style={{
          padding: "0.5rem 1rem",
          borderRadius: "6px",
          border: "none",
          cursor: loading ? "wait" : "pointer",
          backgroundColor: "#3b82f6",
          color: "white",
          fontWeight: 600,
          marginBottom: "1rem",
        }}
      >
        {loading ? "Generando predicciones..." : "Generar predicciones de ruido"}
      </button>

      {error && (
        <div
          style={{
            marginTop: "0.5rem",
            padding: "0.5rem",
            borderRadius: "6px",
            backgroundColor: "#7f1d1d",
            color: "#fee2e2",
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* MÉTRICAS */}
      {metrics && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.75rem",
            borderRadius: "6px",
            backgroundColor: "#1f2937",
          }}
        >
          <h4 style={{ marginBottom: "0.5rem" }}>Métricas del modelo</h4>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.9rem" }}>
            <li>R²: {metrics.r2?.toFixed ? metrics.r2.toFixed(4) : metrics.r2}</li>
            <li>MSE: {metrics.mse?.toFixed ? metrics.mse.toFixed(4) : metrics.mse}</li>
            <li>
              RMSE: {metrics.rmse?.toFixed ? metrics.rmse.toFixed(4) : metrics.rmse}
            </li>
            <li>MAE: {metrics.mae?.toFixed ? metrics.mae.toFixed(4) : metrics.mae}</li>
            <li>Total muestras: {metrics.n_total}</li>
            <li>Train: {metrics.n_train} | Test: {metrics.n_test}</li>
          </ul>
        </div>
      )}

      {/* GRÁFICOS */}
      {plots && (
        <div style={{ marginTop: "1rem" }}>
          <h4 style={{ marginBottom: "0.5rem" }}>Gráficos generados</h4>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
              gap: "1rem",
            }}
          >
            {/* Serie temporal */}
            {plots.time_series && (
              <div
                style={{
                  padding: "0.5rem",
                  borderRadius: "6px",
                  backgroundColor: "#111827",
                  border: "1px solid #374151",
                }}
              >
                <div
                  style={{
                    marginBottom: "0.5rem",
                    fontSize: "0.9rem",
                    fontWeight: 600,
                  }}
                >
                  Serie temporal: Real vs Predicho
                </div>
                <img
                  src={`${BACKEND_BASE_URL}${plots.time_series}`}
                  alt="Serie temporal ruido"
                  style={{
                    width: "100%",
                    height: "auto",
                    borderRadius: "4px",
                    backgroundColor: "#000",
                  }}
                />
              </div>
            )}

            {/* Dispersión */}
            {plots.scatter && (
              <div
                style={{
                  padding: "0.5rem",
                  borderRadius: "6px",
                  backgroundColor: "#111827",
                  border: "1px solid #374151",
                }}
              >
                <div
                  style={{
                    marginBottom: "0.5rem",
                    fontSize: "0.9rem",
                    fontWeight: 600,
                  }}
                >
                  Dispersión Real vs Predicho
                </div>
                <img
                  src={`${BACKEND_BASE_URL}${plots.scatter}`}
                  alt="Dispersión real vs predicho"
                  style={{
                    width: "100%",
                    height: "auto",
                    borderRadius: "4px",
                    backgroundColor: "#000",
                  }}
                />
              </div>
            )}

            {/* Errores */}
            {plots.errors && (
              <div
                style={{
                  padding: "0.5rem",
                  borderRadius: "6px",
                  backgroundColor: "#111827",
                  border: "1px solid #374151",
                }}
              >
                <div
                  style={{
                    marginBottom: "0.5rem",
                    fontSize: "0.9rem",
                    fontWeight: 600,
                  }}
                >
                  Error (residuales) en el tiempo
                </div>
                <img
                  src={`${BACKEND_BASE_URL}${plots.errors}`}
                  alt="Errores en el tiempo"
                  style={{
                    width: "100%",
                    height: "auto",
                    borderRadius: "4px",
                    backgroundColor: "#000",
                  }}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictNoiseButton;
