const MyApplications = ({ token, onViewContract }) => {
    const [applications, setApplications] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [selectedAppId, setSelectedAppId] = React.useState(null);

    React.useEffect(() => {
        const fetchApplications = async () => {
            try {
                setLoading(true);
                const response = await fetch(`${API_BASE_URL}/api/loan_applications`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.message || 'No se pudieron cargar las solicitudes.');
                }
                const data = await response.json();
                setApplications(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (token && !selectedAppId) { // Only fetch list if no detail is being viewed
            fetchApplications();
        }
    }, [token, selectedAppId]);

    if (selectedAppId) {
        return <LoanStatementView token={token} applicationId={selectedAppId} onBack={() => setSelectedAppId(null)} />;
    }

    if (loading) return <p>Cargando solicitudes...</p>;
    if (error) return <p className="error" style={{color: 'red'}}>{error}</p>;

    return (
        <div>
            <h3>Mis Solicitudes de Préstamo</h3>
            {applications.length === 0 ? (
                <p>No tienes solicitudes de préstamo todavía.</p>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Producto</th>
                            <th>Monto Solicitado</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {applications.map(app => (
                            <tr key={app.id}>
                                <td>
                                    {app.status === 'Desembolsada' ? (
                                        <button className="link-button" onClick={() => setSelectedAppId(app.id)}>
                                            #{app.id} (Ver Estado de Cuenta)
                                        </button>
                                    ) : (
                                        `#${app.id}`
                                    )}
                                </td>
                                <td>{app.product_name}</td>
                                <td>${app.amount_requested.toFixed(2)}</td>
                                <td>{app.status}</td>
                                <td>
                                    {['Aprobada', 'Desembolsada'].includes(app.status) && (
                                        <button onClick={() => onViewContract(app.id)}>
                                            Ver Contrato
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};