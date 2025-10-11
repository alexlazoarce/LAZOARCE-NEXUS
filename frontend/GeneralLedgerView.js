const GeneralLedgerView = ({ token, onShowJournal }) => {
    const [ledger, setLedger] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchLedger = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/accounting/general-ledger`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) throw new Error('No se pudo cargar el libro mayor.');
                const data = await response.json();
                setLedger(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchLedger();
    }, [token]);

    if (loading) return <p>Cargando libro mayor...</p>;
    if (error) return <p className="error" style={{color: 'red'}}>{error}</p>;

    return (
        <div>
            <h3>Libro Mayor</h3>
            <button onClick={onShowJournal}>Ver Libro Diario</button>
            <hr />
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr>
                        <th style={{ textAlign: 'left' }}>Cuenta</th>
                        <th style={{ textAlign: 'left' }}>Categoría</th>
                        <th style={{ textAlign: 'right' }}>Saldo</th>
                    </tr>
                </thead>
                <tbody>
                    {ledger.map(account => (
                        <tr key={account.account_id}>
                            <td>{account.account_name}</td>
                            <td>{account.account_category}</td>
                            <td style={{ textAlign: 'right' }}>${account.balance.toFixed(2)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};