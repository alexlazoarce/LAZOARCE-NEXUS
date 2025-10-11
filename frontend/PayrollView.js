function PayrollView({ token }) {
    const [periodName, setPeriodName] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);
    const [error, setError] = React.useState('');
    const [result, setResult] = React.useState(null);

    const handleCalculatePayroll = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        setResult(null);
        try {
            const res = await fetch(`${API_BASE_URL}/api/payroll/calculate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ period_name: periodName })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Error al calcular la planilla');
            setResult(data);
            alert('Planilla calculada y registrada en contabilidad.');
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ marginTop: '2em' }}>
            <h2>Calcular Planilla</h2>
            <form onSubmit={handleCalculatePayroll}>
                <input type="text" value={periodName} onChange={(e) => setPeriodName(e.target.value)} placeholder="Nombre del Período (ej. Enero 2025)" required />
                <button type="submit" disabled={isLoading}>{isLoading ? 'Calculando...' : 'Ejecutar Cálculo'}</button>
            </form>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {result && (
                <div>
                    <h3>Resultados del Cálculo (ID: {result.log_id})</h3>
                    <ul>
                        <li><strong>Total Bruto:</strong> ${result.totals.total_gross.toFixed(2)}</li>
                        <li><strong>Total Neto a Pagar:</strong> ${result.totals.total_net.toFixed(2)}</li>
                        <li><strong>Total Retenciones:</strong> ${(result.totals.total_isss_employee + result.totals.total_afp_employee + result.totals.total_renta).toFixed(2)}</li>
                    </ul>
                </div>
            )}
        </div>
    );
}