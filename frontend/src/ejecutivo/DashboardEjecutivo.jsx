import React, { useState, useEffect } from "react";

import PredictNoiseButton from "../components/PredictNoiseButton";
import UploadCsvButton from "../components/UploadCsvButton";
import CsvChartsGallery from "../components/CsvChartsGallery";

const StatCard = ({ title, value, unit = "" }) => (
  <div className="bg-gray-50 p-4 rounded-lg shadow">
    <h3 className="text-sm font-medium text-gray-500 truncate">{title}</h3>
    <p className="mt-1 text-3xl font-semibold text-gray-900">
      {value ?? "N/A"}
      {value !== null && value !== undefined && unit && (
        <span className="text-lg font-medium"> {unit}</span>
      )}
    </p>
  </div>
);

function DashboardEjecutivo({ user, onLogout, setView }) {
  const [stats, setStats] = useState(null);
  const [latestUplinks, setLatestUplinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [chartUrls, setChartUrls] = useState({
    laeq: null,
    lai: null,
    laimax: null,
    series_chart: null,
  });

  const [csvStatus, setCsvStatus] = useState("");

  // ============================
  // Carga inicial de stats + uplinks
  // ============================
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [statsRes, uplinksRes] = await Promise.all([
          fetch("http://localhost:8070/api/dashboard/stats"),
          fetch("http://localhost:8070/api/dashboard/latest-uplinks"),
        ]);

        if (!statsRes.ok || !uplinksRes.ok) {
          throw new Error("Una o más peticiones a la API fallaron.");
        }

        const statsData = await statsRes.json();
        const uplinksData = await uplinksRes.json();

        setStats(statsData);
        setLatestUplinks(uplinksData);
      } catch (err) {
        console.error(err);
        setError(
          "No se pudieron cargar los datos del dashboard. ¿Está la API funcionando?"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // ============================
  // WebSocket: escuchar finalización del worker
  // ============================
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.hostname;
    const port = "8070";
    const wsUrl = `${protocol}://${host}:${port}/ws/notifications`;

    let socket;

    try {
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log("[WS] Conectado a", wsUrl);
      };

      socket.onmessage = (event) => {
        console.log("[WS] RAW:", event.data);

        let data;
        try {
          data = JSON.parse(event.data);
        } catch (e) {
          console.error("[WS] Error parseando mensaje:", e);
          setCsvStatus("Mensaje recibido del worker, pero no se pudo interpretar.");
          return;
        }

        // Aceptamos tanto summary como status por si el backend está usando otro nombre
        if (data.type === "csv_completed") {
          const summary = data.summary || data.status || data;

          console.log("[WS] csv_completed summary:", summary);

          const charts = (summary && summary.charts) || {};
          const seriesChart = summary && summary.series_chart;

          setChartUrls({
            laeq: charts.laeq || null,
            lai: charts.lai || null,
            laimax: charts.laimax || null,
            series_chart: seriesChart || null,
          });

          // Mensaje para el usuario
          if (summary && typeof summary.processed !== "undefined") {
            setCsvStatus(
              `Procesamiento completado: ${summary.processed} filas leídas, ` +
                `${summary.sound_rows ?? 0} mediciones de ruido registradas.`
            );
          } else {
            setCsvStatus(
              "Procesamiento del CSV completado. Revisa los gráficos y la actividad reciente."
            );
          }
        } else {
          console.log("[WS] Mensaje no relacionado con CSV:", data);
        }
      };

      socket.onerror = (err) => {
        console.error("[WS] Error:", err);
      };

      socket.onclose = () => {
        console.log("[WS] Conexión cerrada");
      };
    } catch (err) {
      console.error("[WS] No se pudo abrir la conexión:", err);
    }

    return () => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* HEADER SUPERIOR */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Dashboard Ejecutivo
            </h1>
            <p className="text-sm text-gray-500">Monitoreo Estratégico GAMC</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-gray-800">
              {user?.fullName}
            </p>
            <p className="text-xs text-gray-500">{user?.email}</p>
            <button
              onClick={onLogout}
              className="mt-2 text-sm text-indigo-600 hover:text-indigo-800"
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      </header>

      {/* CONTENIDO PRINCIPAL */}
      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8 space-y-8">
          {loading && (
            <p className="text-center text-gray-600">Cargando datos...</p>
          )}

          {error && <p className="text-center text-red-500">{error}</p>}

          {!loading && !error && stats && (
            <>
              {/* FILA 1: RESUMEN + CARGA CSV */}
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                {/* Resumen General */}
                <section className="bg-white p-6 rounded-lg shadow xl:col-span-2">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg leading-6 font-medium text-gray-900">
                        Resumen General
                      </h3>
                      <p className="mt-1 text-sm text-gray-500">
                        Indicadores clave del parque de dispositivos y niveles
                        de ruido.
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <StatCard
                      title="Total de Dispositivos"
                      value={stats.total_devices}
                    />
                    <StatCard
                      title="Promedio de Ruido (24h)"
                      value={stats.avg_laeq_24h}
                      unit="dB"
                    />
                    <StatCard
                      title="Batería Baja (&lt;20%)"
                      value={stats.low_battery_devices}
                      unit="dispositivos"
                    />
                    <StatCard
                      title="Nivel de Batería Promedio"
                      value={stats.avg_battery_level}
                      unit="%"
                    />
                  </div>
                </section>

                {/* Card de carga de CSV */}
                <section className="bg-white p-6 rounded-lg shadow flex flex-col justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-1">
                      Carga de datos (CSV)
                    </h3>
                    <p className="text-sm text-gray-500 mb-4">
                      Sube archivos CSV con mediciones de ruido para alimentar
                      el sistema y actualizar los indicadores automáticamente.
                    </p>
                  </div>

                  {/* Botón de subida con callback */}
                  <UploadCsvButton onStatusChange={setCsvStatus} />

                  {/* Botón de predicción */}
                  <PredictNoiseButton />

                  {/* Mensaje de estado del CSV */}
                  {csvStatus && (
                    <p className="mt-3 text-sm text-gray-700">{csvStatus}</p>
                  )}
                </section>
              </div>

              {/* FILA 2: ACTIVIDAD RECIENTE */}
              <section className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">
                      Actividad Reciente
                    </h3>
                    <p className="text-sm text-gray-500">
                      Últimos uplinks recibidos por los dispositivos en campo.
                    </p>
                  </div>
                </div>

                <div className="mt-4 overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Dispositivo
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Fecha y Hora
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Batería
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Ruido (LAeq)
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {latestUplinks.map((uplink, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {uplink.device_name ?? "N/A"}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {uplink.time
                              ? new Date(uplink.time).toLocaleString()
                              : "N/A"}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {typeof uplink.battery_level === "number"
                              ? `${uplink.battery_level.toFixed(1)}%`
                              : "N/A"}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {typeof uplink.laeq === "number"
                              ? `${uplink.laeq.toFixed(2)} dB`
                              : "N/A"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}

          {/* SECCIÓN: Gráficos generados por el worker (último CSV procesado) */}
          {(chartUrls.laeq ||
            chartUrls.lai ||
            chartUrls.laimax ||
            chartUrls.series_chart) && (
            <section className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
              {chartUrls.series_chart && (
                <div className="bg-white p-4 rounded-lg shadow">
                  <h3 className="text-md font-medium text-gray-900 mb-2">
                    Niveles de sonido por dispositivo (series)
                  </h3>
                  <img
                    src={`http://localhost:8070${chartUrls.series_chart}`}
                    alt="Gráfico de series de sonido"
                    className="w-full h-auto rounded-md border"
                  />
                </div>
              )}

              <div className="bg-white p-4 rounded-lg shadow space-y-4">
                <h3 className="text-md font-medium text-gray-900">
                  Resumen diario de ruido
                </h3>

                {chartUrls.laeq && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">
                      LAeq diario (nivel registrado)
                    </p>
                    <img
                      src={`http://localhost:8070${chartUrls.laeq}`}
                      alt="Gráfico LAeq diario"
                      className="w-full h-auto rounded-md border"
                    />
                  </div>
                )}

                {chartUrls.lai && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">
                      LAI diario (promedio)
                    </p>
                    <img
                      src={`http://localhost:8070${chartUrls.lai}`}
                      alt="Gráfico LAI diario"
                      className="w-full h-auto rounded-md border"
                    />
                  </div>
                )}

                {chartUrls.laimax && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">
                      LAImax diario (pico máximo)
                    </p>
                    <img
                      src={`http://localhost:8070${chartUrls.laimax}`}
                      alt="Gráfico LAImax diario"
                      className="w-full h-auto rounded-md border"
                    />
                  </div>
                )}
              </div>
            </section>
          )}

          {/* SECCIÓN: Galería de gráficos históricos */}
          <section className="mt-8 bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-1">
              Historial de gráficos generados por CSV
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Estos gráficos se cargan desde los archivos PNG generados en el
              servidor cuando el worker procesa los CSV (carpeta{" "}
              <code>/data/charts</code>).
            </p>
            <CsvChartsGallery />
          </section>

          {/* BOTÓN INFERIOR: GESTIÓN DE USUARIOS */}
          <div className="flex justify-end mt-4">
            <button
              onClick={() => setView("user_management")}
              className="inline-flex items-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition duration-150"
            >
              <span className="mr-2">👥</span>
              Gestión de Usuarios
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default DashboardEjecutivo;
