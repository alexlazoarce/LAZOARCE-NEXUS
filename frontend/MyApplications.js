const API_BASE_URL = 'http://127.0.0.1:5000';

function MyApplications({ token }) {
    const [applications, setApplications] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchApplications = async () => {
            try {
                setError('');
                const res = await fetch(`${API_BASE_URL}/api/applications`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.msg || 'No se pudieron cargar las solicitudes.');
                }
                setApplications(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchApplications();
    }, [token]); // El efecto se ejecuta cada vez que el token cambia

    if (loading) {
        return <p>Cargando solicitudes...</p>;
    }

    if (error) {
        return <p style={{ color: 'red' }}>Error: {error}</p>;
    }

    return (
        <div className="applications-container">
            <h3>Historial de Solicitudes de Préstamo</h3>
            {applications.length === 0 ? (
                <p>No has realizado ninguna solicitud de préstamo todavía.</p>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>ID Solicitud</th>
                            <th>Producto</th>
                            <th>Monto Solicitado</th>
                            <th>Plazo (Meses)</th>
                            <th>Fecha</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {applications.map((app) => (
                            <tr key={app.id}>
                                <td>{app.id}</td>
                                <td>{app.product_name}</td>
                                <td>${app.requested_amount.toFixed(2)}</td>
                                <td>{app.requested_term}</td>
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