function MyApplications({ token }) {
    const [applications, setApplications] = React.useState([]);
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(true);

    React.useEffect(() => {
        const fetchApplications = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/loan-applications`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.msg || 'Failed to fetch applications');
                }
                setApplications(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };
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
            {applications.length === 0 ? (
                <p>No has enviado ninguna solicitud.</p>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>ID de Solicitud</th>
                            <th>Producto</th>
                            <th>Monto Solicitado</th>
                            <th>Fecha</th>
                            <th>Estado</th>
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
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}