function GeneralLedgerView({ token }) {
    const [ledgerData, setLedgerData] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    const fetchLedger = () => {
        setIsLoading(true);
        fetch(`${API_BASE_URL}/api/accounting/general-ledger`, { headers: { 'Authorization': `Bearer ${token}` } })
            .then(res => res.ok ? res.json() : Promise.reject(res.json()))
            .then(setLedgerData)
            .catch(err => err.then(e => setError(e.msg)))
            .finally(() => setIsLoading(false));
    };

    React.useEffect(fetchLedger, [token]);

    if (isLoading) return <p>Cargando libro mayor...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

    return (
        <div>
            <h2>Libro Mayor General</h2>
            <button onClick={fetchLedger}>Recargar</button>
            <table>
                <thead>
                    <tr>
                        <th>Código</th><th>Cuenta</th><th>Débitos</th><th>Créditos</th><th>Saldo Final</th>
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
        </div>
    );
}