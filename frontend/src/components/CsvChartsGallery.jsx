// frontend/src/components/CsvChartsGallery.jsx

import React, { useEffect, useState } from "react";

const API_CHARTS_URL = "http://localhost:8070/api/charts";
const BACKEND_BASE_URL = "http://localhost:8070";

const CsvChartsGallery = () => {
  const [charts, setCharts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCharts = async () => {
    setLoading(true);
    setError(null);

    try {
      const resp = await fetch(API_CHARTS_URL);
      if (!resp.ok) {
        throw new Error("No se pudieron obtener los gráficos de CSV procesados");
      }
      const data = await resp.json();
      setCharts(data.charts || []);
    } catch (err) {
      console.error("Error obteniendo gráficos:", err);
      setError(err.message || "Error desconocido al cargar gráficos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharts();
  }, []);

  return (
    <div
      style={{
        marginTop: "1rem",
        padding: "1rem",
        borderRadius: "8px",
        border: "1px solid #374151",
        backgroundColor: "#0f172a",
        color: "#e5e7eb",
      }}
    >
      <div
        style={{
          marginBottom: "0.75rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.5rem",
        }}
      >
        <h3 style={{ margin: 0, fontSize: "1rem" }}>
          Gráficos generados a partir del último CSV procesado
        </h3>
        <button
          onClick={fetchCharts}
          disabled={loading}
          style={{
            padding: "0.35rem 0.8rem",
            borderRadius: "6px",
            border: "none",
            cursor: loading ? "wait" : "pointer",
            backgroundColor: "#10b981",
            color: "white",
            fontSize: "0.8rem",
            fontWeight: 600,
          }}
        >
          {loading ? "Actualizando..." : "Actualizar"}
        </button>
      </div>

      {error && (
        <div
          style={{
            marginBottom: "0.75rem",
            padding: "0.5rem",
            borderRadius: "6px",
            backgroundColor: "#7f1d1d",
            color: "#fee2e2",
            fontSize: "0.85rem",
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {charts.length === 0 && !loading && !error && (
        <p style={{ fontSize: "0.9rem", color: "#9ca3af" }}>
          No hay gráficos disponibles todavía. Sube un CSV y espera a que el worker
          termine de procesarlo 📂📊.
        </p>
      )}

      {charts.length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "1rem",
          }}
        >
          {charts.map((chart) => (
            <div
              key={chart.filename}
              style={{
                padding: "0.5rem",
                borderRadius: "6px",
                backgroundColor: "#020617",
                border: "1px solid #1f2937",
              }}
            >
              <div
                style={{
                  marginBottom: "0.5rem",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                  color: "#e5e7eb",
                  wordBreak: "break-all",
                }}
              >
                {chart.filename}
              </div>
              <img
                src={`${BACKEND_BASE_URL}${chart.url}`}
                alt={chart.filename}
                style={{
                  width: "100%",
                  height: "auto",
                  borderRadius: "4px",
                  backgroundColor: "#000",
                }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CsvChartsGallery;
