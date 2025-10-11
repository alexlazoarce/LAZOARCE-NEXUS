const AuditLogView = ({ token }) => {
    const [logs, setLogs] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [filter, setFilter] = React.useState('');

    React.useEffect(() => {
        const fetchLogs = async () => {
            try {
                setLoading(true);
                const response = await fetch(`${API_BASE_URL}/api/audit-logs`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) throw new Error('No se pudo cargar el registro de auditoría.');
                const data = await response.json();
                setLogs(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchLogs();
    }, [token]);

    const filteredLogs = logs.filter(log =>
        filter ? log.action.toUpperCase().includes(filter.toUpperCase()) : true
    );

    if (loading) return <p>Cargando registros de auditoría...</p>;
    if (error) return <p className="error">{error}</p>;

    return (
        <div>
            <h3>Registro de Auditoría del Sistema</h3>
            <input
                type="text"
                placeholder="Filtrar por acción (ej. LOAN_STATUS_CHANGE)"
                value={filter}
                onChange={e => setFilter(e.target.value)}
                style={{marginBottom: '10px', width: '300px'}}
            />
            <table style={{ width: '100%' }}>
                <thead>
                    <tr>
                        <th>Fecha y Hora</th>
                        <th>Usuario</th>
                        <th>Acción</th>
                        <th>Detalles</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredLogs.map(log => (
                        <tr key={log.id}>
                            <td>{new Date(log.timestamp).toLocaleString()}</td>
                            <td>{log.user_email}</td>
                            <td>{log.action}</td>
                            <td>{log.details}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};