function GeneralLedgerView({ token }) {
    const [ledgerData, setLedgerData] = React.useState([]);
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);

    const fetchLedgerData = async () => {
        if (!token) {
            setError('Token no proporcionado.');
            return;
        }
        setError('');
        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/accounting/general-ledger`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.msg || 'Failed to fetch ledger data');
            }
            setLedgerData(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    // Fetch data automatically when the component mounts
    React.useEffect(() => {
        fetchLedgerData();
    }, [token]);


    return (
        <div className="ledger-view">
            <h2>Libro Mayor General</h2>
            <button onClick={fetchLedgerData} disabled={isLoading}>
                {isLoading ? 'Recargando...' : 'Recargar Libro Mayor'}
            </button>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            {isLoading && ledgerData.length === 0 && <p>Cargando libro mayor...</p>}

            {ledgerData.length > 0 ? (
                <table>
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Nombre de Cuenta</th>
                            <th>Total Débitos</th>
                            <th>Total Créditos</th>
                            <th>Saldo Final</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ledgerData.map(acc => (
                            <tr key={acc.account_code}>
                                <td>{acc.account_code}</td>
                                <td>{acc.account_name}</td>
                                <td>${acc.total_debits.toFixed(2)}</td>
                                <td>${acc.total_credits.toFixed(2)}</td>
                                <td>${acc.final_balance.toFixed(2)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : (
                !isLoading && <p>No hay datos en el libro mayor para mostrar.</p>
            )}
        </div>
    );
}