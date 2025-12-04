import React, { useState, useEffect } from 'react';

const FormInput = ({ id, label, type = 'text', value, onChange, placeholder, required = false, autoFocus = false }) => {
    return (
        <div className="mb-4">
            <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
                {label}
            </label>
            <input
                type={type}
                name={id}
                id={id}
                value={value}
                onChange={onChange}
                placeholder={placeholder}
                required={required}
                autoFocus={autoFocus}
                className="block w-full rounded-md border-gray-300 border p-2 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
        </div>
    );
};

function UserForm({ title, initialData, onSubmit, onCancel, isLoading, message }) {
    const [formData, setFormData] = useState({
        fullName: '',
        username: '',
        email: '',
        role: 'Operativo',
        password: '',
        confirmPassword: '',
    });

    const isEditing = !!initialData?._id;

    useEffect(() => {
        if (isEditing) {
            setFormData({
                ...initialData,
                password: '',
                confirmPassword: '',
            });
        }
    }, [initialData, isEditing]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            alert("Las contraseñas no coinciden.");
            return;
        }
        onSubmit(formData);
    };

    return (
        <div className="max-w-4xl mx-auto p-4 md:p-8">
            <div className="bg-white shadow-2xl rounded-xl border border-gray-100 p-8">
                <div className="flex items-center mb-6">
                    <button
                        onClick={onCancel}
                        className="p-2 mr-4 text-gray-500 hover:text-indigo-600 transition duration-150 rounded-full hover:bg-gray-100"
                        title="Volver"
                        disabled={isLoading}
                    >
                        <span className="text-xl">←</span>
                    </button>
                    <h2 className="text-2xl font-bold text-gray-800">{title}</h2>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {message && (
                        <div className={`p-3 rounded-lg text-sm font-medium ${message.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                            {message}
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <FormInput id="fullName" label="Nombre Completo" value={formData.fullName} onChange={handleChange} required autoFocus />
                        <FormInput id="username" label="Nombre de Usuario" value={formData.username} onChange={handleChange} required />
                        <FormInput id="email" label="Correo Electrónico" type="email" value={formData.email} onChange={handleChange} required />
                        
                        <div>
                            <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
                            <select
                                id="role"
                                name="role"
                                value={formData.role}
                                onChange={handleChange}
                                className="block w-full rounded-md border-gray-300 border p-2 text-gray-900 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            >
                                <option value="Operativo">Operativo</option>
                                <option value="Ejecutivo">Ejecutivo</option>
                            </select>
                        </div>

                        <FormInput
                            id="password"
                            label={isEditing ? "Nueva Contraseña (dejar en blanco para no cambiar)" : "Contraseña"}
                            type="password"
                            value={formData.password}
                            onChange={handleChange}
                            required={!isEditing}
                        />
                        <FormInput
                            id="confirmPassword"
                            label="Confirmar Contraseña"
                            type="password"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            required={!isEditing || formData.password}
                        />
                    </div>
                    
                    <div className="pt-4">
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="group relative flex justify-center items-center w-full md:w-auto rounded-md border border-transparent bg-indigo-600 py-2 px-6 text-sm font-medium text-white shadow-lg transition duration-300 ease-in-out hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
                        >
                            {isLoading ? (
                                <span className="animate-spin">⏳</span>
                            ) : (
                                <>{isEditing ? '💾 Guardar Cambios' : '➕ Registrar Usuario'}</>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default UserForm;