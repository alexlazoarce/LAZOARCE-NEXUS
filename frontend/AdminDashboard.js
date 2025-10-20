const AdminDashboard = ({ token, onManagePayments }) => {
    const [applications, setApplications] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [disbursementSources, setDisbursementSources] = React.useState({}); // { appId: 'Bancos' | 'Caja' }

    const fetchApplications = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/applications`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('Error al cargar solicitudes');
            const data = await response.json();
            setApplications(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchApplications();
    }, [token]);

    const handleSourceChange = (appId, source) => {
        setDisbursementSources(prev => ({ ...prev, [appId]: source }));
    };

    const handleStatusChange = async (appId, newStatus) => {
        try {
            let body = { status: newStatus };
            if (newStatus === 'Desembolsada') {
                const source = disbursementSources[appId] || 'Bancos'; // Default to Bancos
                body.disbursement_source = source;
            }

            const response = await fetch(`${API_BASE_URL}/api/applications/${appId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(body),
            });
            if (!response.ok) {
                 const errData = await response.json();
                 throw new Error(errData.message || 'No se pudo actualizar el estado.');
            }
            // Refresh the list after successful update
            fetchApplications();
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    };

    if (loading) return <p>Cargando panel de administrador...</p>;
    if (error) return <p className="error" style={{color: 'red'}}>{error}</p>;

    return (
        <div>
            <h3>Panel de Administración - Todas las Solicitudes</h3>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Solicitante</th>
                        <th>Producto</th>
                        <th>Monto</th>
                        <th>Estado</th>
                        <th>Fecha Solicitud</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {applications.map(app => (
                        <tr key={app.id}>
                            <td>{app.id}</td>
                            <td>{app.applicant_name}</td>
                            <td>{app.product_name}</td>
                            <td>${app.amount_requested.toFixed(2)}</td>
                            <td>{app.status}</td>
                            <td>{new Date(app.application_date).toLocaleString()}</td>
                            <td>
                                {app.status === 'Pendiente' && (
                                    <>
                                        <button onClick={() => handleStatusChange(app.id, 'Aprobada')}>Aprobar</button>
                                        <button onClick={() => handleStatusChange(app.id, 'Rechazada')}>Rechazar</button>
                                    </>
                                )}
                                 {app.status === 'Aprobada' && (
                                    <>
                                        <select
                                            onChange={(e) => handleSourceChange(app.id, e.target.value)}
                                            value={disbursementSources[app.id] || 'Bancos'}
                                            style={{marginRight: '5px'}}
                                        >
                                            <option value="Bancos">Desde Bancos</option>
                                            <option value="Caja">Desde Caja</option>
                                        </select>
                                        <button onClick={() => handleStatusChange(app.id, 'Desembolsada')}>
                                            Desembolsar
                                        </button>
                                    </>
                                )}
                                {app.status === 'Desembolsada' && (
                                    <button onClick={() => onManagePayments(app)}>
                                        Gestionar Pagos
                                    </button>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};