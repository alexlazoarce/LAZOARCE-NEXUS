const API_BASE_URL = 'http://127.0.0.1:5000';

function PaymentHistory({ token, applicationId, onBack }) {
    const [payments, setPayments] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        if (!applicationId) return;

        const fetchPayments = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/applications/${applicationId}/payments`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.msg || 'No se pudo cargar el historial de pagos.');
                setPayments(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchPayments();
    }, [token, applicationId]);

    if (loading) return <p>Cargando historial de pagos...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

    return (
        <div className="payment-history-container">
            <button onClick={onBack} className="back-button">← Volver a Mis Solicitudes</button>
            <h3>Historial de Pagos para el Préstamo #{applicationId}</h3>
            {payments.length === 0 ? (
                <p>No se han registrado pagos para este préstamo.</p>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>ID Pago</th>
                            <th>Monto</th>
                            <th>Fecha de Pago</th>
                            <th>Método</th>
                            <th>Registrado por</th>
                        </tr>
                    </thead>
                    <tbody>
                        {payments.map(p => (
                            <tr key={p.id}>
                                <td>{p.id}</td>
                                <td>${p.amount.toFixed(2)}</td>
                                <td>{new Date(p.payment_date).toLocaleString()}</td>
                                <td>{p.payment_method}</td>
                                <td>{p.recorded_by}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}