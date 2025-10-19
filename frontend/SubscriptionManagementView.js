// frontend/SubscriptionManagementView.js

function SubscriptionManagementView() {
    const [tenants, setTenants] = React.useState([]);
    const [selectedTenant, setSelectedTenant] = React.useState(null);
    const [subscriptions, setSubscriptions] = React.useState([]);
    const [systemModules, setSystemModules] = React.useState([]);
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);

    const API_URL = 'http://127.0.0.1:5001/api';

    const getAuthToken = () => localStorage.getItem('accessToken');

    // In a real app, you would fetch tenants and modules from dedicated endpoints.
    // For now, we'll hardcode/mock some of this data for simplicity.
    const fetchTenants = () => {
        // This is a placeholder. A real endpoint to list all tenants would be needed.
        // For now, let's assume the Super Admin knows the tenant ID.
        // We will manually input the tenant ID to manage.
    };

    const fetchSystemModules = () => {
        // This is a placeholder. A real endpoint to list all system modules would be needed.
        const modules = [
            'LAN-GP1', 'LAN-REC7', 'LAN-CB7', 'LAN-BKS1', 'LAN-V1A',
            'LAN-OBD2', 'LAN-AT5', 'LAN-NR4', 'LAN-SUB1', 'LAN-LIC1',
            'LAN-GYM1', 'LAN-BAR1', 'LAN-AGT5', 'LAN-N8N1', 'LAN-MKE1'
        ];
        setSystemModules(modules);
    };

    const fetchSubscriptions = (tenantId) => {
        if (!tenantId) return;
        setIsLoading(true);
        fetch(`${API_URL}/subscriptions/tenant/${tenantId}`, {
            headers: { 'Authorization': `Bearer ${getAuthToken()}` }
        })
        .then(response => {
            if (!response.ok) throw new Error('Error al cargar las suscripciones.');
            return response.json();
        })
        .then(data => {
            setSubscriptions(data);
            setIsLoading(false);
        })
        .catch(err => {
            setError(err.message);
            setIsLoading(false);
            console.error(err);
        });
    };

    React.useEffect(() => {
        // On component mount, we'd fetch initial data.
        fetchTenants();
        fetchSystemModules();
    }, []);

    const handleTenantSelect = (tenantId) => {
        const id = parseInt(tenantId, 10);
        if (isNaN(id)) {
            setSelectedTenant(null);
            setSubscriptions([]);
            return;
        }
        setSelectedTenant({ id: id, name: `Inquilino #${id}` }); // Mock tenant object
        fetchSubscriptions(id);
    };

    const handleGrantSubscription = (moduleCode, trialDays = null) => {
        if (!selectedTenant) return;

        const endDate = new Date();
        if (trialDays) {
            endDate.setDate(endDate.getDate() + trialDays);
        } else {
            endDate.setFullYear(endDate.getFullYear() + 1);
        }

        const subscriptionData = {
            tenant_id: selectedTenant.id,
            module_code: moduleCode,
            end_date: endDate.toISOString()
        };

        fetch(`${API_URL}/subscriptions/grant`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify(subscriptionData)
        })
        .then(response => {
            if (!response.ok) throw new Error('Error al otorgar la suscripción.');
            return response.json();
        })
        .then(() => {
            fetchSubscriptions(selectedTenant.id); // Refresh the list
        })
        .catch(err => {
            setError(err.message);
            console.error(err);
        });
    };

    // A function to revoke would be very similar, calling a different endpoint.

    return (
        <div style={{ fontFamily: 'Arial, sans-serif', padding: '20px', color: '#333' }}>
            <h1 style={{ color: '#1a365d' }}>Gestión de Suscripciones (LAN-SUB1)</h1>
            <p>Esta vista es solo para Super Administradores.</p>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <div style={{ marginBottom: '20px' }}>
                <label htmlFor="tenant-select"><strong>Seleccionar Inquilino (por ID): </strong></label>
                <input
                    type="number"
                    id="tenant-select"
                    placeholder="Escriba el ID del Inquilino"
                    onChange={(e) => handleTenantSelect(e.target.value)}
                    style={{ padding: '8px', fontSize: '16px' }}
                />
            </div>

            {selectedTenant ? (
                <div>
                    <h2 style={{ color: '#1a365d' }}>Suscripciones para: {selectedTenant.name}</h2>
                    {isLoading ? <p>Cargando...</p> : (
                        <div style={{ display: 'flex', gap: '40px' }}>
                            <div>
                                <h3>Módulos Subscritos</h3>
                                <ul style={{ listStyleType: 'disc', paddingLeft: '20px' }}>
                                    {subscriptions.filter(s => s.status === 'active').map(s => (
                                        <li key={s.module_code} style={{ marginBottom: '5px' }}>
                                            <strong>{s.module_code}</strong> ({s.module_name}) - Vence: {s.end_date ? new Date(s.end_date).toLocaleDateString() : 'Nunca'}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <div>
                                <h3>Módulos Disponibles para Activar</h3>
                                <ul style={{ listStyleType: 'none', padding: 0 }}>
                                    {systemModules
                                        .filter(moduleCode => !subscriptions.some(s => s.module_code === moduleCode && s.status === 'active'))
                                        .map(moduleCode => (
                                        <li key={moduleCode} style={{ marginBottom: '10px' }}>
                                            {moduleCode}
                                            <button
                                                onClick={() => handleGrantSubscription(moduleCode)}
                                                style={{ marginLeft: '10px', backgroundColor: '#059669', color: 'white', border: 'none', borderRadius: '5px', padding: '5px 10px', cursor: 'pointer' }}>
                                                Activar por 1 Año
                                            </button>
                                            <button
                                                onClick={() => handleGrantSubscription(moduleCode, 15)}
                                                style={{ marginLeft: '5px', backgroundColor: '#fbbf24', color: 'black', border: 'none', borderRadius: '5px', padding: '5px 10px', cursor: 'pointer' }}>
                                                Prueba 15 Días
                                            </button>
                                            <button
                                                onClick={() => handleGrantSubscription(moduleCode, 30)}
                                                style={{ marginLeft: '5px', backgroundColor: '#fbbf24', color: 'black', border: 'none', borderRadius: '5px', padding: '5px 10px', cursor: 'pointer' }}>
                                                Prueba 30 Días
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    )}
                </div>
            ) : (
                <p>Por favor, ingrese el ID de un inquilino para ver y gestionar sus suscripciones.</p>
            )}
        </div>
    );
}
