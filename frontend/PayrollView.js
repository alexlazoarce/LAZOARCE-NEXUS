const PayrollView = ({ token, onViewPaySlips }) => {
    const [startDate, setStartDate] = React.useState('');
    const [endDate, setEndDate] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const [message, setMessage] = React.useState('');
    const [error, setError] = React.useState('');
    const [lastPayrollLogId, setLastPayrollLogId] = React.useState(null);

    const handleRunPayroll = async () => {
        setLoading(true);
        setMessage('');
        setError('');
        setLastPayrollLogId(null);

        try {
            const response = await fetch(`${API_BASE_URL}/api/payroll/calculate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ start_date: startDate, end_date: endDate }),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Error al procesar la nómina.');
            }
            setMessage(`¡Éxito! ${data.message} Se procesaron ${data.employees_processed} empleados.`);
            setLastPayrollLogId(data.payroll_log_id);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h3>Procesamiento de Nómina</h3>
            <div style={{ border: '1px solid #ccc', padding: '10px' }}>
                <h4>Ejecutar Nómina para un Período</h4>
                <label>Fecha de Inicio:</label>
                <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required />
                <label>Fecha de Fin:</label>
                <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} required />

                <button onClick={handleRunPayroll} disabled={loading || !startDate || !endDate}>
                    {loading ? 'Procesando...' : 'Ejecutar Cálculo de Nómina'}
                </button>

                {message && <p style={{ color: 'green' }}>{message}</p>}
                {error && <p style={{ color: 'red' }}>{error}</p>}

                {lastPayrollLogId && (
                    <button onClick={() => onViewPaySlips(lastPayrollLogId)} style={{marginTop: '10px'}}>
                        Ver Recibos de Pago Generados
                    </button>
                )}
            </div>
        </div>
    );
};