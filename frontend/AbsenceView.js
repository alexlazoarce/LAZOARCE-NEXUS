const AbsenceView = ({ token }) => {
    const [balance, setBalance] = React.useState(null);
    const [requests, setRequests] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    // Form state
    const [absenceType, setAbsenceType] = React.useState('Vacaciones');
    const [startDate, setStartDate] = React.useState('');
    const [endDate, setEndDate] = React.useState('');
    const [comments, setComments] = React.useState('');

    const fetchData = async () => {
        try {
            setLoading(true);
            const [balanceRes, requestsRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/absences/balance`, { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/api/absences/requests`, { headers: { 'Authorization': `Bearer ${token}` } })
            ]);
            if (!balanceRes.ok) throw new Error('No se pudo cargar el saldo de vacaciones.');
            if (!requestsRes.ok) throw new Error('No se pudieron cargar las solicitudes.');

            const balanceData = await balanceRes.json();
            const requestsData = await requestsRes.json();

            setBalance(balanceData.vacation_balance);
            setRequests(requestsData);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchData();
    }, [token]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/absences/requests`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ absence_type: absenceType, start_date: startDate, end_date: endDate, comments })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'No se pudo crear la solicitud.');

            // Reset form and refresh data
            setAbsenceType('Vacaciones');
            setStartDate('');
            setEndDate('');
            setComments('');
            fetchData();
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) return <p>Cargando gestión de ausencias...</p>;

    return (
        <div>
            <h3>Gestión de Vacaciones y Ausencias (LAN-V1A)</h3>

            <div style={{ padding: '10px', backgroundColor: '#f0f0f0', marginBottom: '20px' }}>
                <strong>Saldo de Vacaciones Disponibles:</strong> {balance !== null ? `${balance} días` : 'Calculando...'}
            </div>

            {error && <p style={{ color: 'red' }}>{error}</p>}

            <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
                <h4>Nueva Solicitud de Ausencia</h4>
                <select value={absenceType} onChange={e => setAbsenceType(e.target.value)}>
                    <option value="Vacaciones">Vacaciones</option>
                    <option value="Enfermedad">Enfermedad</option>
                    <option value="Personal">Asunto Personal</option>
                </select>
                <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required />
                <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} required />
                <input type="text" value={comments} onChange={e => setComments(e.target.value)} placeholder="Comentarios (opcional)" />
                <button type="submit">Enviar Solicitud</button>
            </form>

            <h4>Historial de Solicitudes</h4>
            <table>
                <thead>
                    <tr>
                        <th>Tipo</th>
                        <th>Desde</th>
                        <th>Hasta</th>
                        <th>Estado</th>
                        <th>Comentarios</th>
                    </tr>
                </thead>
                <tbody>
                    {requests.map(req => (
                        <tr key={req.id}>
                            <td>{req.absence_type}</td>
                            <td>{req.start_date}</td>
                            <td>{req.end_date}</td>
                            <td>{req.status}</td>
                            <td>{req.comments}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};
