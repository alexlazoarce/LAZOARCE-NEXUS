const AdminDashboard = ({ token, onManagePayments }) => {
    const [applications, setApplications] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [disbursementSources, setDisbursementSources] = React.useState({}); // { appId: 'Bancos' | 'Caja' }
    const [filterStatus, setFilterStatus] = React.useState('');
    const [filterStartDate, setFilterStartDate] = React.useState('');
    const [filterEndDate, setFilterEndDate] = React.useState('');

    const fetchApplications = async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            if (filterStatus) params.append('status', filterStatus);
            if (filterStartDate) params.append('start_date', filterStartDate);
            if (filterEndDate) params.append('end_date', filterEndDate);

            const response = await fetch(`${API_BASE_URL}/api/loan_applications?${params.toString()}`, {
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

    const handleApprove = async (appId) => {
        // This function would call a new endpoint to approve the loan
        // For now, we'll just update the status locally for simplicity
        try {
            const response = await fetch(`${API_BASE_URL}/api/loan_applications/${appId}/approve`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudo aprobar la solicitud.');
            fetchApplications();
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    };

    const handleReject = async (appId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/loan_applications/${appId}/reject`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudo rechazar la solicitud.');
            fetchApplications();
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    };

    const handleDisburse = async (appId) => {
        try {
            const source = disbursementSources[appId] || 'Bancos';
            const response = await fetch(`${API_BASE_URL}/api/loan_applications/${appId}/disburse`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({ disbursement_source: source }),
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'No se pudo desembolsar el préstamo.');
            }
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
            <div style={{ margin: '10px 0', padding: '10px', border: '1px solid #ccc' }}>
                <h4>Filtrar Solicitudes</h4>
                <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                    <option value="">Todos los Estados</option>
                    <option value="Pendiente">Pendiente</option>
                    <option value="Aprobada">Aprobada</option>
                    <option value="Rechazada">Rechazada</option>
                    <option value="Desembolsada">Desembolsada</option>
                </select>
                <input type="date" value={filterStartDate} onChange={e => setFilterStartDate(e.target.value)} />
                <input type="date" value={filterEndDate} onChange={e => setFilterEndDate(e.target.value)} />
                <button onClick={fetchApplications}>Filtrar</button>
                <button onClick={() => {
                    setFilterStatus('');
                    setFilterStartDate('');
                    setFilterEndDate('');
                }}>Limpiar</button>
            </div>
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
                                        <button onClick={() => handleApprove(app.id)}>Aprobar</button>
                                        <button onClick={() => handleReject(app.id)}>Rechazar</button>
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
                                        <button onClick={() => handleDisburse(app.id)}>
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