const BalanceSheetView = ({ token }) => {
    const [report, setReport] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchBalanceSheet = async () => {
            try {
                setLoading(true);
                const response = await fetch(`${API_BASE_URL}/api/reports/balance-sheet`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) throw new Error('No se pudo cargar el Balance General.');
                const data = await response.json();
                setReport(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchBalanceSheet();
    }, [token]);

    if (loading) return <p>Cargando Balance General...</p>;
    if (error) return <p className="error" style={{ color: 'red' }}>{error}</p>;
    if (!report) return null;

    const isBalanced = Math.abs(report.total_assets - report.total_liabilities_and_equity) < 0.01;

    return (
        <div>
            <h3>Balance General (LAN-BKS1)</h3>
            <div style={{ display: 'flex', justifyContent: 'space-around' }}>
                {/* Assets */}
                <div style={{ width: '45%' }}>
                    <h4>Activos</h4>
                    <table style={{ width: '100%' }}>
                        <tbody>
                            {report.assets.map(acc => (
                                <tr key={acc.name}>
                                    <td>{acc.name}</td>
                                    <td style={{ textAlign: 'right' }}>${acc.balance.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                        <tfoot>
                            <tr style={{ fontWeight: 'bold', borderTop: '1px solid black' }}>
                                <td>Total Activos</td>
                                <td style={{ textAlign: 'right' }}>${report.total_assets.toFixed(2)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>

                {/* Liabilities & Equity */}
                <div style={{ width: '45%' }}>
                    <h4>Pasivos</h4>
                    <table style={{ width: '100%' }}>
                        <tbody>
                            {report.liabilities.map(acc => (
                                <tr key={acc.name}>
                                    <td>{acc.name}</td>
                                    <td style={{ textAlign: 'right' }}>${acc.balance.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                        <tfoot>
                            <tr style={{ fontWeight: 'bold', borderTop: '1px solid black' }}>
                                <td>Total Pasivos</td>
                                <td style={{ textAlign: 'right' }}>${report.total_liabilities.toFixed(2)}</td>
                            </tr>
                        </tfoot>
                    </table>

                    <h4 style={{ marginTop: '20px' }}>Patrimonio</h4>
                    <table style={{ width: '100%' }}>
                        <tbody>
                            {report.equity.map(acc => (
                                <tr key={acc.name}>
                                    <td>{acc.name}</td>
                                    <td style={{ textAlign: 'right' }}>${acc.balance.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                        <tfoot>
                            <tr style={{ fontWeight: 'bold', borderTop: '1px solid black' }}>
                                <td>Total Patrimonio</td>
                                <td style={{ textAlign: 'right' }}>${report.total_equity.toFixed(2)}</td>
                            </tr>
                            <tr style={{ fontWeight: 'bold', borderTop: '2px solid black', marginTop: '5px' }}>
                                <td>Total Pasivos + Patrimonio</td>
                                <td style={{ textAlign: 'right' }}>${report.total_liabilities_and_equity.toFixed(2)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>
            <div style={{ textAlign: 'center', marginTop: '20px', fontWeight: 'bold', color: isBalanced ? 'green' : 'red' }}>
                {isBalanced ? 'La Ecuación Contable está Balanceada' : '¡La Ecuación Contable NO está Balanceada!'}
            </div>
        </div>
    );
};
