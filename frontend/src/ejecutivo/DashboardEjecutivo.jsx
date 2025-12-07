import React, { useState, useEffect } from 'react';

const StatCard = ({ title, value, unit = '' }) => (
    <div className="bg-gray-50 p-4 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-500 truncate">{title}</h3>
        <p className="mt-1 text-3xl font-semibold text-gray-900">
            {value ?? 'N/A'}
            {value !== null && unit && <span className="text-lg font-medium"> {unit}</span>}
        </p>
    </div>
);

function DashboardEjecutivo({ user, onLogout, setView }) {
    const [stats, setStats] = useState(null);
    const [latestUplinks, setLatestUplinks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                // Hacemos las peticiones a la API en paralelo
                const [statsRes, trendRes] = await Promise.all([
                    fetch('http://localhost:8070/api/dashboard/stats'),
                    fetch('http://localhost:8070/api/dashboard/latest-uplinks')
                ]);

                // Verificamos que ambas respuestas sean exitosas (status 200-299)
                if (!statsRes.ok || !trendRes.ok) {
                    // Si alguna falla, lanzamos un error para que lo capture el bloque catch
                    throw new Error('Una o más peticiones a la API fallaron.');
                }

                const statsData = await statsRes.json();
                const trendData = await trendRes.json();

                setStats(statsData);
                setLatestUplinks(trendData);
            } catch (err) {
                setError('No se pudieron cargar los datos del dashboard. ¿Está la API funcionando?');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    return (
        <div className="min-h-screen bg-gray-100">
            <header className="bg-white shadow">
                <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            Dashboard Ejecutivo
                        </h1>
                        <p className="text-sm text-gray-500">Monitoreo Estratégico GAMC</p>
                    </div>
                    <div className="text-right">
                        <p className="text-sm font-medium text-gray-800">{user?.fullName}</p>
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
            <main>
                <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                    {loading && <p className="text-center">Cargando datos...</p>}
                    {error && <p className="text-center text-red-500">{error}</p>}
                    
                    {!loading && !error && stats && (
                        <>
                            {/* Sección de KPIs */}
                            <h3 className="text-lg leading-6 font-medium text-gray-900">Resumen General</h3>
                            <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                                <StatCard title="Total de Dispositivos" value={stats.total_devices} />
                                <StatCard title="Promedio de Ruido (24h)" value={stats.avg_laeq_24h} unit="dB" />
                                <StatCard title="Batería Baja (<20%)" value={stats.low_battery_devices} unit="dispositivos" />
                                <StatCard title="Nivel de Batería Promedio" value={stats.avg_battery_level} unit="%" />
                            </div>

                            {/* Tabla de Actividad Reciente */}
                            <div className="mt-8 bg-white p-6 rounded-lg shadow">
                                <h3 className="text-lg font-medium text-gray-900">Actividad Reciente</h3>
                                <div className="mt-4 overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dispositivo</th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha y Hora</th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Batería</th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ruido (LAeq)</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {latestUplinks.map((uplink, index) => (
                                                <tr key={index}>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{uplink.device_name ?? 'N/A'}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(uplink.time).toLocaleString()}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{uplink.battery_level?.toFixed(1) ?? 'N/A'}%</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{uplink.laeq?.toFixed(2) ?? 'N/A'} dB</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </>
                    )}

                    <div className="mt-8">
                        <button
                            onClick={() => setView('user_management')}
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