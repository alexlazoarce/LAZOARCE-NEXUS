const SuperAdminDashboard = ({ token }) => {
    const [tenants, setTenants] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [newCompanyName, setNewCompanyName] = React.useState('');

    const fetchTenants = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/super-admin/tenants`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudieron cargar los tenants.');
            const data = await response.json();
            setTenants(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchTenants();
    }, [token]);

    const handleCreateTenant = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${API_BASE_URL}/api/super-admin/tenants`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ company_name: newCompanyName })
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.message || 'Error al crear el tenant.');
            }
            setNewCompanyName('');
            fetchTenants();
            alert('¡Nuevo tenant creado con éxito!');
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) return <p>Cargando panel de Super Admin...</p>;

    return (
        <div>
            <h3>Panel de Super Administrador - Gestión de Empresas (Tenants)</h3>
            {error && <p style={{color: 'red'}}>{error}</p>}

            <form onSubmit={handleCreateTenant} style={{border: '1px solid #ccc', padding: '10px', marginBottom: '20px'}}>
                <h4>Registrar Nueva Empresa</h4>
                <input
                    value={newCompanyName}
                    onChange={e => setNewCompanyName(e.target.value)}
                    placeholder="Nombre de la Empresa"
                    required
                />
                <button type="submit">Crear Tenant</button>
            </form>

            <h4>Empresas Registradas</h4>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nombre de la Empresa</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
                    {tenants.map(t => (
                        <tr key={t.id}>
                            <td>{t.id}</td>
                            <td>{t.company_name}</td>
                            <td>{t.is_active ? 'Activo' : 'Inactivo'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};