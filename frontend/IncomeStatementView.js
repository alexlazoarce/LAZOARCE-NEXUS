const IncomeStatementView = ({ token }) => {
    const [report, setReport] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchIncomeStatement = async () => {
            try {
                setLoading(true);
                const response = await fetch(`${API_BASE_URL}/api/reports/income-statement`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) throw new Error('No se pudo cargar el Estado de Resultados.');
                const data = await response.json();
                setReport(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchIncomeStatement();
    }, [token]);

    if (loading) return <p>Cargando Estado de Resultados...</p>;
    if (error) return <p className="error" style={{ color: 'red' }}>{error}</p>;
    if (!report) return null;

    return (
        <div>
            <h3>Estado de Resultados (LAN-BKS1)</h3>

            <h4>Ingresos</h4>
            <table style={{ width: '100%' }}>
                <tbody>
                    {report.income.map(acc => (
                        <tr key={acc.name}>
                            <td>{acc.name}</td>
                            <td style={{ textAlign: 'right' }}>${acc.balance.toFixed(2)}</td>
                        </tr>
                    ))}
                </tbody>
                <tfoot>
                    <tr style={{ fontWeight: 'bold', borderTop: '1px solid black' }}>
                        <td>Total Ingresos</td>
                        <td style={{ textAlign: 'right' }}>${report.total_income.toFixed(2)}</td>
                    </tr>
                </tfoot>
            </table>

            <h4 style={{ marginTop: '20px' }}>Gastos</h4>
            <table style={{ width: '100%' }}>
                <tbody>
                    {report.expenses.length === 0 ? (
                        <tr><td colSpan="2">No se registraron gastos.</td></tr>
                    ) : (
                        report.expenses.map(acc => (
                            <tr key={acc.name}>
                                <td>{acc.name}</td>
                                <td style={{ textAlign: 'right' }}>${acc.balance.toFixed(2)}</td>
                            </tr>
                        ))
                    )}
                </tbody>
                <tfoot>
                    <tr style={{ fontWeight: 'bold', borderTop: '1px solid black' }}>
                        <td>Total Gastos</td>
                        <td style={{ textAlign: 'right' }}>${report.total_expenses.toFixed(2)}</td>
                    </tr>
                </tfoot>
            </table>

            <hr />
            <div style={{ textAlign: 'right', marginTop: '10px', fontSize: '1.2em' }}>
                <strong>{report.net_income >= 0 ? 'Ingreso Neto' : 'Pérdida Neta'}:</strong>
                <strong style={{ marginLeft: '20px', color: report.net_income >= 0 ? 'green' : 'red' }}>
                    ${report.net_income.toFixed(2)}
                </strong>
            </div>
        </div>
    );
};
