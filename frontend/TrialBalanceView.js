const TrialBalanceView = ({ token, onShowJournal }) => {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchTrialBalance = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/accounting/trial-balance`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) throw new Error('No se pudo cargar la balanza de comprobación.');
                const responseData = await response.json();
                setData(responseData);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchTrialBalance();
    }, [token]);

    if (loading) return <p>Cargando balanza de comprobación...</p>;
    if (error) return <p className="error" style={{color: 'red'}}>{error}</p>;
    if (!data) return null;

    const { report, total_debits, total_credits, is_balanced } = data;

    return (
        <div>
            <h3>Balanza de Comprobación</h3>
            <button onClick={onShowJournal}>Volver al Libro Diario</button>
            <hr />
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr>
                        <th style={{ textAlign: 'left' }}>Cuenta</th>
                        <th style={{ textAlign: 'right' }}>Débitos</th>
                        <th style={{ textAlign: 'right' }}>Créditos</th>
                    </tr>
                </thead>
                <tbody>
                    {report.map(row => (
                        <tr key={row.account_name}>
                            <td>{row.account_name}</td>
                            <td style={{ textAlign: 'right' }}>${row.debits.toFixed(2)}</td>
                            <td style={{ textAlign: 'right' }}>${row.credits.toFixed(2)}</td>
                        </tr>
                    ))}
                </tbody>
                <tfoot>
                    <tr style={{ fontWeight: 'bold', borderTop: '2px solid black' }}>
                        <td>TOTALES</td>
                        <td style={{ textAlign: 'right' }}>${total_debits.toFixed(2)}</td>
                        <td style={{ textAlign: 'right' }}>${total_credits.toFixed(2)}</td>
                    </tr>
                    {is_balanced && (
                        <tr>
                            <td colSpan="3" style={{ textAlign: 'center', color: 'green', paddingTop: '10px' }}>
                                ✨ La balanza está cuadrada ✨
                            </td>
                        </tr>
                    )}
                    {!is_balanced && (
                         <tr>
                            <td colSpan="3" style={{ textAlign: 'center', color: 'red', paddingTop: '10px' }}>
                                ⚠️ ¡Atención! La balanza no está cuadrada.
                            </td>
                        </tr>
                    )}
                </tfoot>
            </table>
        </div>
    );
};