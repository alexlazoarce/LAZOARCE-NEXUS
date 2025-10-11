function MyApplications({ token, onViewDetails, onViewContract }) {
    const [applications, setApplications] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    const fetchApplications = () => {
        setIsLoading(true);
        fetch(`${API_BASE_URL}/api/loan-applications`, { headers: { 'Authorization': `Bearer ${token}` } })
            .then(res => res.ok ? res.json() : Promise.reject(res.json()))
            .then(setApplications)
            .catch(err => err.then(e => setError(e.msg)))
            .finally(() => setIsLoading(false));
    };

    React.useEffect(fetchApplications, [token]);

    if (isLoading) return <p>Cargando solicitudes...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

    return (
        <div>
            <h2>Mis Solicitudes de Préstamo</h2>
            <button onClick={fetchApplications}>Recargar</button>
            <table>
                <thead>
                    <tr>
                        <th>ID</th><th>Producto</th><th>Monto</th><th>Fecha</th><th>Estado</th><th>Firma</th><th>Acciones</th>
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
                            <td>{app.signature_status}</td>
                            <td>
                                {app.status === 'Desembolsado' && <button onClick={() => onViewContract(app.id)}>Contrato/Firma</button>}
                                <button onClick={() => onViewDetails(app.id)} style={{marginLeft: '5px'}}>Detalles</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}