import React, { useState, useEffect, useCallback } from 'react';
import LoginPage from './login/LoginPage';
import DashboardEjecutivo from './ejecutivo/DashboardEjecutivo';
import DashboardOperativo from './operativo/DashboardOperativo';
import UserManagement from './ejecutivo/user management/UserManagement';
import UserForm from './ejecutivo/user management/UserForm';


import WebSocketNotifications from "./WebSocketNotifications";


// URL base de tu backend. DEBES cambiar 'http://localhost:8080' por la URL/puerto real de tu servicio backend-1
const API_BASE_URL = 'http://localhost:8070/api'; 


function App() {
    // El estado inicial es 'cargando' hasta que verifiquemos si hay una sesión activa
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [view, setView] = useState('loading'); // 'loading', 'login', 'dashboard_ejecutivo', 'dashboard_operativo', 'user_management', 'user_create', 'user_edit'
    const [users, setUsers] = useState([]);
    const [editingUser, setEditingUser] = useState(null); // Usuario que se está editando
    const [message, setMessage] = useState(''); // Mensajes de éxito o error
    const [isLoading, setIsLoading] = useState(false);

    const [wsEventCounter, setWsEventCounter] = useState(0);
const [toastMsg, setToastMsg] = useState(null);

const handleWsMessage = useCallback((payload) => {
  let messageText = "";
  let shouldTriggerReload = false;

  // Si el backend mandó texto plano:
  if (typeof payload === "string") {
    messageText = payload;
    // Puedes decidir si eso recarga o no
    shouldTriggerReload = true;
  } else {
    // Mensaje estructurado
    switch (payload.type) {
      case "CSV_COMPLETED": {
        const s = payload.summary || {};
        messageText =
          payload.text ||
          `CSV procesado: ${s.valid_rows ?? s.processed ?? 0} filas válidas, ` +
            `${s.inserted_uplinks ?? 0} uplinks, ${s.sound_rows ?? 0} sonidos.`;
        // Este sí queremos que dispare recarga de dashboards/tablas
        shouldTriggerReload = true;
        break;
      }

      case "USER_CREATED":
        messageText = payload.text || "Nuevo usuario creado.";
        shouldTriggerReload = true; // refrescar vista de usuarios
        break;

      case "USER_UPDATED":
        messageText = payload.text || "Usuario actualizado.";
        shouldTriggerReload = true;
        break;

      case "USER_DELETED":
        messageText = payload.text || "Usuario eliminado.";
        shouldTriggerReload = true;
        break;

      default:
        messageText = payload.text || JSON.stringify(payload);
        shouldTriggerReload = false;
        break;
    }
  }

  if (messageText) {
    setToastMsg(messageText);
    setTimeout(() => setToastMsg(null), 5000);
  }

  if (shouldTriggerReload) {
    setWsEventCounter((prev) => prev + 1);
  }
}, []);


    const handleLoginSuccess = (data) => {
        // Guardamos el token en localStorage para persistir la sesión
        localStorage.setItem('authToken', data.access_token); 
        // Guardamos la info del usuario también para recuperarla en recargas de página
        localStorage.setItem('userInfo', JSON.stringify(data.user_info));

        // Guardamos la información del usuario en el estado
        setUser(data.user_info);
        setIsAuthenticated(true);

        // Decidimos qué dashboard mostrar según el rol
        if (data.user_info.role === 'Ejecutivo') {
            setView('dashboard_ejecutivo');
        } else {
            setView('dashboard_operativo');
        }
        setMessage(`¡Bienvenido/a, ${data.user_info.fullName}!`);
        setIsLoading(false);
    };

    const handleLoginError = (errorMessage) => {
        // Limpiamos cualquier token antiguo y mostramos el error
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        setMessage(`Error de inicio de sesión: ${errorMessage}`);
        setIsAuthenticated(false);
        setUser(null);
        setIsLoading(false);
    };

    // Efecto para verificar la sesión al cargar la app
    useEffect(() => {
        const token = localStorage.getItem('authToken');
        const userInfo = localStorage.getItem('userInfo');

        if (token && userInfo) {
            const parsedUser = JSON.parse(userInfo);
            setUser(parsedUser);
            setIsAuthenticated(true);
            // Redirigir al dashboard correcto al recargar la página
            if (parsedUser.role === 'Ejecutivo') {
                setView('dashboard_ejecutivo');
            } else {
                setView('dashboard_operativo');
            }
        } else {
            setView('login'); // Si no hay token, ir a la página de login
        }
    }, []); // Se ejecuta solo una vez al montar el componente

    const handleLogout = () => {
        localStorage.removeItem('authToken'); // Limpiamos el token
        localStorage.removeItem('userInfo');
        setIsAuthenticated(false);
        setView('login'); // Llevamos al usuario a la página de login
        setUser(null);
        setUsers([]);
        setMessage('Sesión cerrada.');
    };

    // --- Lógica CRUD de Usuarios ---

    const handleCreateUser = async (newUserData) => {
        setIsLoading(true);
        setMessage('');
        const token = localStorage.getItem('authToken');
        try {
            // Preparamos los datos para enviar, excluyendo confirmPassword
            const { confirmPassword, ...userDataToSend } = newUserData;

            const response = await fetch(`${API_BASE_URL}/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(userDataToSend),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Error al crear usuario.');
            
            setMessage('Usuario creado con éxito.');
            // Forzar recarga de la lista de usuarios
            setView('loading'); // truco para forzar el re-render
            setTimeout(() => setView('user_management'), 10);
        } catch (error) {
            console.error("Error al crear usuario:", error);
            setMessage(`Error: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleUpdateUser = async (updatedUserData) => {
        setIsLoading(true);
        setMessage('');
        const token = localStorage.getItem('authToken');
        try {
            // Preparamos los datos para enviar, excluyendo campos que el backend no espera
            const { _id, confirmPassword, ...userDataToSend } = updatedUserData;

            const response = await fetch(`${API_BASE_URL}/users/${_id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(userDataToSend),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Error al actualizar usuario.');

            setMessage('Usuario actualizado con éxito.');
            setView('user_management');
            setEditingUser(null);
        } catch (error) {
            console.error("Error al actualizar usuario:", error);
            setMessage(`Error: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteUser = async (userId) => {
        if (!window.confirm('¿Estás seguro de que quieres eliminar este usuario? Esta acción no se puede deshacer.')) {
            return;
        }
        setIsLoading(true);
        setMessage('');
        const token = localStorage.getItem('authToken');
        try {
            const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al eliminar usuario.');
            }
            setMessage('Usuario eliminado con éxito.');
            // Forzar recarga de la lista de usuarios
            setView('loading'); // truco para forzar el re-render
            setTimeout(() => setView('user_management'), 10);
        } catch (error) {
            console.error("Error al eliminar usuario:", error);
            setMessage(`Error: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleEditClick = (userToEdit) => {
        setEditingUser(userToEdit);
        setView('user_edit');
    };

    const handleCancelForm = () => {
        setEditingUser(null);
        setMessage('');
        setView('user_management');
    };

    const renderContent = () => {
        switch (view) {
            case 'login':
                return <LoginPage 
                    onLoginSuccess={handleLoginSuccess} 
                    onLoginError={handleLoginError}
                    isLoading={isLoading}
                    message={message}
                />;
            case 'dashboard_ejecutivo':
                return <DashboardEjecutivo user={user} onLogout={handleLogout} setView={setView} wsEventCounter={wsEventCounter} />;
            case 'dashboard_operativo':
                // Pasamos setView para que el dashboard pueda navegar a otras vistas, como la de gestión de usuarios.
                return <DashboardOperativo user={user} onLogout={handleLogout} setView={setView} wsEventCounter={wsEventCounter} />;
            case 'user_management':
                return <UserManagement user={user} setView={setView} onEdit={handleEditClick} onDelete={handleDeleteUser} wsEventCounter={wsEventCounter} />;
            case 'user_create':
                return <UserForm 
                    title="Registrar Nuevo Usuario"
                    onSubmit={handleCreateUser}
                    onCancel={handleCancelForm}
                    isLoading={isLoading}
                    message={message}
                />;
            case 'user_edit':
                return <UserForm
                    title="Editar Usuario"
                    initialData={editingUser}
                    onSubmit={handleUpdateUser}
                    onCancel={handleCancelForm}
                    isLoading={isLoading}
                    message={message}
                />;
            case 'loading':
                return (
                    <div className="flex min-h-screen items-center justify-center">
                        <span className="animate-spin text-3xl">⏳</span>
                        <p className="ml-3 text-gray-600">Cargando...</p>
                    </div>
                );
            default:
                // Si el estado es inválido o no está autenticado, volvemos al login.
                return <LoginPage onLoginSuccess={handleLoginSuccess} onLoginError={handleLoginError} isLoading={isLoading} message={message} />;
        }
    };

 return (

  <div className="min-h-screen bg-gray-50 font-sans antialiased">
    {renderContent()}

    {isAuthenticated && (
      <>
        <WebSocketNotifications onMessage={handleWsMessage} />

        {toastMsg && (
          <div className="fixed top-4 right-4 z-[9999] max-w-sm rounded-lg bg-white shadow-lg border border-gray-200 px-4 py-3 text-sm text-gray-800">
            <div className="flex items-start">
              <span className="mr-2 mt-0.5 text-green-500">✅</span>
              <div>
                <p className="font-semibold">Procesamiento completado</p>
                <p className="text-xs text-gray-600 mt-1">
                  {toastMsg}
                </p>
              </div>
            </div>
          </div>
        )}
      </>
    )}
  </div>
);
}

export default App;