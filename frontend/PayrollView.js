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
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ period_name: periodName })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Failed to calculate payroll');
            setResult(data);
            alert('Planilla calculada y registrada en contabilidad exitosamente.');
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ border: '1px solid #ccc', padding: '1em', marginTop: '2em' }}>
            <h2>Calcular Planilla</h2>
            <form onSubmit={handleCalculatePayroll}>
                <input
                    type="text"
                    value={periodName}
                    onChange={(e) => setPeriodName(e.target.value)}
                    placeholder="Nombre del Período (ej. Enero 2025)"
                    required
                />
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Calculando...' : 'Ejecutar Cálculo de Planilla'}
                </button>
            </form>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {result && (
                <div style={{ marginTop: '1em' }}>
                    <h3>Resultados del Cálculo</h3>
                    <p><strong>Mensaje:</strong> {result.msg}</p>
                    <p><strong>ID del Registro de Planilla:</strong> {result.payroll_log_id}</p>
                    <h4>Totales:</h4>
                    <ul>
                        <li><strong>Total Bruto:</strong> ${result.totals.total_gross.toFixed(2)}</li>
                        <li><strong>Total Neto a Pagar:</strong> ${result.totals.total_net.toFixed(2)}</li>
                        <li><strong>Total ISSS (Empleado + Patronal):</strong> ${(result.totals.total_isss_employee + result.totals.total_isss_employer).toFixed(2)}</li>
                        <li><strong>Total AFP (Empleado + Patronal):</strong> ${(result.totals.total_afp_employee + result.totals.total_afp_employer).toFixed(2)}</li>
                        <li><strong>Total Renta Retenida:</strong> ${result.totals.total_renta.toFixed(2)}</li>
                    </ul>
                </div>
            )}
        </div>
    );
}