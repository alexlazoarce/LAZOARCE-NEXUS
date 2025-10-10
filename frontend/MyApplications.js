function MyApplications({ token, onViewDetails, onViewContract }) {
    const [applications, setApplications] = React.useState([]);
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(true);

    const fetchApplications = async () => {
        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/loan-applications`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Failed to fetch applications');
            setApplications(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    React.useEffect(() => {
        fetchApplications();
    }, [token]);

    if (isLoading) {
        return <p>Cargando solicitudes...</p>;
    }

    if (error) {
        return <p style={{ color: 'red' }}>{error}</p>;
    }

    return (
        <div>
            <h2>Mis Solicitudes de Préstamo</h2>
            <button onClick={fetchApplications}>Recargar</button>
            {applications.length === 0 ? (
                <p>No has enviado ninguna solicitud.</p>
            ) : (
                <table style={{marginTop: '1em'}}>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Producto</th>
                            <th>Monto</th>
                            <th>Fecha</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {applications.map(app => (
                            <tr key={app.id}>
                                <td>{app.id}</td>
                                <td>{app.product_name}</td>
                                <td>${app.requested_amount.toFixed(2)}</td>
                                <td>{new Date(app.application_date).toLocaleDateString()}</td>
                                <td>{app.status}</td>
                                <td>
                                    {app.status === 'Desembolsado' && (
                                        <>
                                            <button onClick={() => onViewDetails(app.id)}>Detalles</button>
                                            <button onClick={() => onViewContract(app.id)} style={{marginLeft: '5px'}}>Contrato</button>
                                        </>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}