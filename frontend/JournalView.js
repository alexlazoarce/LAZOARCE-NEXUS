const JournalView = ({ token, onShowLedger }) => {
    const [entries, setEntries] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchJournal = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/accounting/journal`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) throw new Error('No se pudo cargar el libro diario.');
                const data = await response.json();
                setEntries(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchJournal();
    }, [token]);

    if (loading) return <p>Cargando libro diario...</p>;
    if (error) return <p className="error" style={{color: 'red'}}>{error}</p>;

    return (
        <div>
            <h3>Libro Diario</h3>
            <button onClick={onShowLedger}>Ver Libro Mayor</button>
            <hr />
            {entries.map(entry => (
                <div key={entry.id} style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
                    <p><strong>Fecha:</strong> {new Date(entry.date).toLocaleString()}</p>
                    <p><strong>Descripción:</strong> {entry.description}</p>
                    <table style={{ width: '100%' }}>
                        <thead>
                            <tr>
                                <th>Cuenta</th>
                                <th style={{ textAlign: 'right' }}>Débito</th>
                                <th style={{ textAlign: 'right' }}>Crédito</th>
                            </tr>
                        </thead>
                        <tbody>
                            {entry.transactions.map((t, index) => (
                                <tr key={index}>
                                    <td>{t.account_name}</td>
                                    <td style={{ textAlign: 'right' }}>
                                        {t.type === 'Debit' ? `$${t.amount.toFixed(2)}` : ''}
                                    </td>
                                    <td style={{ textAlign: 'right' }}>
                                        {t.type === 'Credit' ? `$${t.amount.toFixed(2)}` : ''}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ))}
        </div>
    );
};