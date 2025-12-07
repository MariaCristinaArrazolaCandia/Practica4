import React, { useState, useEffect, useCallback } from 'react';

// URL base de tu backend.
const API_BASE_URL = 'http://localhost:8070/api';

function UserManagement({ user, setView, onEdit, onDelete , wsEventCounter}) {
    const [users, setUsers] = useState([]);
    const [message, setMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const fetchUsers = useCallback(async () => {
        setIsLoading(true);
        setMessage('');
        const token = localStorage.getItem('authToken');

        try {
            const response = await fetch(`${API_BASE_URL}/users`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al cargar usuarios.');
            }

            const data = await response.json();
            setUsers(data);
        } catch (error) {
            setMessage(`Error: ${error.message}`);
            setUsers([]);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);
    
    useEffect(() => {
    if (wsEventCounter > 0) {
      fetchUsers();
    }
  }, [wsEventCounter]);

    const goBackToDashboard = () => {
        if (user.role === 'Ejecutivo') {
            setView('dashboard_ejecutivo');
        } else {
            setView('dashboard_operativo');
        }
    };

    return (
        <div className="max-w-7xl mx-auto p-4 md:p-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
                <div className="flex items-center">
                    <button
                        onClick={goBackToDashboard}
                        className="p-2 mr-4 text-gray-500 hover:text-indigo-600 transition duration-150 rounded-full hover:bg-gray-100"
                        title="Volver al Dashboard"
                    >
                        <span className="text-2xl">←</span>
                    </button>
                    <div>
                        <h1 className="text-3xl font-extrabold text-gray-900">Gestión de Usuarios</h1>
                        <p className="text-sm text-gray-500 mt-1">
                            Lista de todos los usuarios del sistema.
                        </p>
                    </div>
                    <div className="flex space-x-3 mt-4 md:mt-0">
                        <button
                            onClick={() => setView('user_create')}
                            className="inline-flex items-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition duration-150 disabled:opacity-50"
                            disabled={isLoading}
                        >
                            <span className="mr-2">➕</span>
                            Nuevo Usuario
                        </button>
                    </div>
                </div>
            </div>

            {message && (
                <div className={`p-3 mb-4 rounded-lg text-sm font-medium ${message.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`} role="alert">
                    {message}
                </div>
            )}

            <div className="bg-white shadow-2xl rounded-xl overflow-hidden border border-gray-100">
                {isLoading ? (
                    <div className="p-10 flex flex-col items-center justify-center">
                        <span className="animate-spin text-3xl">⏳</span>
                        <p className="mt-2 text-gray-600">Cargando usuarios...</p>
                    </div>
                ) : users.length === 0 && !message ? (
                    <div className="p-10 text-center text-gray-500">
                        No hay usuarios registrados.
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre Completo</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rol</th>
                                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {users.map((u) => (
                                    <tr key={u._id} className="hover:bg-indigo-50 transition duration-100">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{u.fullName}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.username}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.email}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                                u.role === 'Ejecutivo' ? 'bg-indigo-100 text-indigo-800' : 'bg-green-100 text-green-800'
                                            }`}>
                                                {u.role}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                                            <button
                                                onClick={() => onEdit(u)}
                                                className="text-indigo-600 hover:text-indigo-900 p-1 rounded-full hover:bg-indigo-100 transition duration-150"
                                                title="Editar"
                                            >
                                                <span className="text-lg">✏️</span>
                                            </button>
                                            <button
                                                onClick={() => onDelete(u._id)}
                                                className="text-red-600 hover:text-red-900 p-1 rounded-full hover:bg-red-100 transition duration-150"
                                                title="Eliminar"
                                            >
                                                <span className="text-lg">🗑️</span>
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

export default UserManagement;