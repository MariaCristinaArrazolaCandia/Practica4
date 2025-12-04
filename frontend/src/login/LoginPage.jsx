import React, { useState } from 'react';

// URL del endpoint de login en tu backend.
// Asegúrate de que el puerto (8070) coincida con tu docker-compose.yml
const API_LOGIN_URL = 'http://localhost:8070/api/users/login';

/**
 * Componente de UI reutilizable para un campo de formulario.
 */
const FormInput = ({ id, label, type = 'text', value, onChange, placeholder, required = false, Icon, autoFocus = false }) => {
    const [showPassword, setShowPassword] = useState(false);
    const inputType = type === 'password' && showPassword ? 'text' : type;

    return (
        <div className="mb-4">
            <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
                {label}
            </label>
            <div className="relative rounded-md shadow-sm">
                {Icon && (
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                        <span className="h-5 w-5 text-gray-400">{Icon}</span>
                    </div>
                )}
                <input
                    type={inputType}
                    name={id}
                    id={id}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                    required={required}
                    autoFocus={autoFocus}
                    className={`block w-full rounded-md border-gray-300 border p-2 ${Icon ? 'pl-10' : 'pl-3'} pr-3 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm`}
                />
                {type === 'password' && (
                    <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="text-gray-400 hover:text-gray-600 focus:outline-none"
                        >
                            {showPassword ? '👁️' : '🚫👁️'}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

/**
 * Página de inicio de sesión que se comunica con el backend.
 */
function LoginPage({ onLoginSuccess, onLoginError, isLoading, message }) {
	const [email, setEmail] = useState('');
	const [password, setPassword] = useState('');

	const handleSubmit = async (e) => {
		e.preventDefault();
		onLoginError(''); // Limpia el mensaje de error anterior al iniciar un nuevo intento

		// FastAPI con OAuth2PasswordRequestForm espera los datos como FormData
		const formData = new FormData();
		formData.append('username', email); // El email se envía en el campo 'username'
		formData.append('password', password);

		try {
			const response = await fetch(API_LOGIN_URL, {
				method: 'POST',
				body: formData,
			});

			const data = await response.json();

			if (response.ok) {
				// Si la respuesta es 2xx (éxito), llamamos a onLoginSuccess
				onLoginSuccess(data);
			} else {
				// Si la respuesta es 4xx o 5xx, llamamos a onLoginError con el detalle del backend
				onLoginError(data.detail || 'Error en el inicio de sesión');
			}
		} catch (error) {
			// Este catch ahora solo se activará para errores de red (ej. servidor caído)
			onLoginError('No se pudo conectar con el servidor. Inténtalo más tarde.');
		}
	};

	return (
		<div className="flex min-h-screen items-center justify-center px-4">
			<div className="w-full max-w-md">
                <div className="text-center mb-10">
                    <span className="mx-auto h-12 w-auto text-indigo-600 text-4xl">⚡</span>
                    <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                        Iniciar Sesión
                    </h2>
                    <p className="mt-2 text-sm text-gray-600">
                        Gestión de Usuarios - Monitoreo GAMC
                    </p>
                </div>

                {/* --- ZONA DE MENSAJES --- */}
                {message && (
                    <div className={`mb-4 p-3 rounded-md text-sm text-center ${message.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                        {message}
                    </div>
                )}

                <form className="space-y-6 bg-white p-8 shadow-2xl rounded-xl border border-gray-100" onSubmit={handleSubmit}>
                    <FormInput
                        id="email"
                        label="Correo Electrónico"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="tu.correo@example.com"
                        required
                        Icon={'✉️'}
                        autoFocus
                    />

                    <FormInput
                        id="password"
                        label="Contraseña"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        Icon={'🔒'}
                    />

                    <div>
                        <button type="submit" disabled={isLoading} className="group relative flex w-full justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-lg transition duration-300 ease-in-out hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50">
                            {isLoading ? <span className="animate-spin">⏳</span> : 'Ingresar'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default LoginPage;