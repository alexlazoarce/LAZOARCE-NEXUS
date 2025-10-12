import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { toast } from 'react-toastify';

const SuperAdminDashboard = () => {
    const [tenants, setTenants] = useState([]);
    const [newTenantName, setNewTenantName] = useState('');
    const [newTenantAdminEmail, setNewTenantAdminEmail] = useState('');
    const [newTenantAdminPassword, setNewTenantAdminPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchTenants = async () => {
        setIsLoading(true);
        try {
            const response = await api.get('/super-admin/tenants');
            setTenants(response.data);
            setError(null);
        } catch (err) {
            const message = err.response?.data?.msg || 'Error al cargar los inquilinos';
            setError(message);
            toast.error(message);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchTenants();
    }, []);

    const handleCreateTenant = async (e) => {
        e.preventDefault();
        if (!newTenantName || !newTenantAdminEmail || !newTenantAdminPassword) {
            toast.warn('Por favor complete todos los campos para crear un inquilino.');
            return;
        }
        setIsLoading(true);
        try {
            const payload = {
                name: newTenantName,
                admin_email: newTenantAdminEmail,
                admin_password: newTenantAdminPassword,
            };
            const response = await api.post('/super-admin/tenants', payload);
            toast.success(response.data.msg || 'Inquilino creado con éxito');
            setNewTenantName('');
            setNewTenantAdminEmail('');
            setNewTenantAdminPassword('');
            fetchTenants(); // Refresh the list
        } catch (err) {
            const message = err.response?.data?.msg || 'Error al crear el inquilino';
            setError(message);
            toast.error(message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="container mt-4">
            <h2>Panel de Super Administrador</h2>
            <p>Gestión de Inquilinos del Sistema.</p>

            {error && <div className="alert alert-danger">{error}</div>}

            <div className="card">
                <div className="card-header">
                    <h4>Crear Nuevo Inquilino</h4>
                </div>
                <div className="card-body">
                    <form onSubmit={handleCreateTenant}>
                        <div className="row">
                            <div className="col-md-4 mb-3">
                                <label htmlFor="tenantName" className="form-label">Nombre del Inquilino</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    id="tenantName"
                                    value={newTenantName}
                                    onChange={(e) => setNewTenantName(e.target.value)}
                                    placeholder="Ej: Mi Nueva Empresa"
                                    required
                                />
                            </div>
                            <div className="col-md-4 mb-3">
                                <label htmlFor="adminEmail" className="form-label">Email del Administrador</label>
                                <input
                                    type="email"
                                    className="form-control"
                                    id="adminEmail"
                                    value={newTenantAdminEmail}
                                    onChange={(e) => setNewTenantAdminEmail(e.target.value)}
                                    placeholder="admin@nuevaempresa.com"
                                    required
                                />
                            </div>
                            <div className="col-md-4 mb-3">
                                <label htmlFor="adminPassword" className="form-label">Contraseña del Administrador</label>
                                <input
                                    type="password"
                                    className="form-control"
                                    id="adminPassword"
                                    value={newTenantAdminPassword}
                                    onChange={(e) => setNewTenantAdminPassword(e.target.value)}
                                    placeholder="Contraseña segura"
                                    required
                                />
                            </div>
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={isLoading}>
                            {isLoading ? 'Creando...' : 'Crear Inquilino'}
                        </button>
                    </form>
                </div>
            </div>

            <div className="card mt-4">
                <div className="card-header">
                    <h4>Inquilinos Existentes</h4>
                </div>
                <div className="card-body">
                    {isLoading && tenants.length === 0 ? (
                        <p>Cargando inquilinos...</p>
                    ) : (
                        <div className="table-responsive">
                            <table className="table table-striped">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Nombre</th>
                                        <th>Fecha de Creación</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {tenants.map((tenant) => (
                                        <tr key={tenant.id}>
                                            <td>{tenant.id}</td>
                                            <td>{tenant.name}</td>
                                            <td>{new Date(tenant.created_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SuperAdminDashboard;