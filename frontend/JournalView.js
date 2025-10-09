const API_BASE_URL = 'http://127.0.0.1:5000';

function JournalView({ token }) {
    const [transactions, setTransactions] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchJournal = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/accounting/journal`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.msg || 'No se pudo cargar el libro diario.');
                setTransactions(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchJournal();
    }, [token]);

    if (loading) return <p>Cargando libro diario...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

    return (
        <div className="journal-container">
            <h3>Libro Diario</h3>
            {transactions.length === 0 ? (
                <p>No hay transacciones registradas.</p>
            ) : (
                transactions.map(t => (
                    <div key={t.transaction_id} className="transaction-card">
                        <div className="transaction-header">
                            <strong>Transacción #{t.transaction_id}</strong>
                            <span>{new Date(t.date).toLocaleString()}</span>
                        </div>
                        <p className="transaction-description"><em>{t.description}</em></p>
                        <table>
                            <thead>
                                <tr>
                                    <th>Cuenta</th>
                                    <th>Débito</th>
                                    <th>Crédito</th>
                                </tr>
                            </thead>
                            <tbody>
                                {t.entries.map(e => (
                                    <tr key={`${t.transaction_id}-${e.account_code}`}>
                                        <td>{e.account_code} - {e.account_name}</td>
                                        <td className="currency">${e.debit.toFixed(2)}</td>
                                        <td className="currency">${e.credit.toFixed(2)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ))
            )}
        </div>
    );
}