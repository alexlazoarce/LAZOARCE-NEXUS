const LoanStatementView = ({ token, applicationId, onBack }) => {
    const [statement, setStatement] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        if (!applicationId) return;
        const fetchStatement = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/applications/${applicationId}/statement`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.message || 'No se pudo cargar el estado de cuenta.');
                }
                const data = await response.json();
                setStatement(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchStatement();
    }, [token, applicationId]);

    if (loading) return <p>Cargando estado de cuenta...</p>;
    if (error) return <p className="error" style={{color: 'red'}}>{error}</p>;
    if (!statement) return null;

    const { loan_summary, loan_status, payments_history } = statement;

    return (
        <div>
            <button onClick={onBack}>← Volver a Mis Solicitudes</button>
            <h3>Estado de Cuenta del Préstamo #{loan_summary.id}</h3>

            <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '20px' }}>
                <div>
                    <p><strong>Monto Total:</strong> ${loan_summary.amount_requested.toFixed(2)}</p>
                    <p><strong>Total Pagado:</strong> ${loan_status.total_paid.toFixed(2)}</p>
                    <p><strong>Saldo Pendiente:</strong> ${loan_status.outstanding_balance.toFixed(2)}</p>
                </div>
                <div>
                    <p><strong>Estado:</strong> <span style={{color: loan_status.status === 'En Mora' ? 'red' : 'green'}}>{loan_status.status}</span></p>
                    <p><strong>Días de Mora:</strong> {loan_status.days_delinquent}</p>
                    <p><strong>Próximo Vencimiento:</strong> {loan_status.next_due_date}</p>
                </div>
            </div>

            <h4>Historial de Pagos</h4>
            <table>
                <thead>
                    <tr>
                        <th>Fecha de Pago</th>
                        <th>Monto Pagado</th>
                        <th>Tipo</th>
                        <th>Registrado por</th>
                    </tr>
                </thead>
                <tbody>
                    {payments_history.length > 0 ? payments_history.map(p => (
                        <tr key={p.id}>
                            <td>{p.payment_date}</td>
                            <td>${p.amount_paid.toFixed(2)}</td>
                            <td>{p.type}</td>
                            <td>{p.registered_by}</td>
                        </tr>
                    )) : (
                        <tr><td colSpan="4">No hay pagos registrados.</td></tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};