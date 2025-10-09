const API_BASE_URL = 'http://127.0.0.1:5000';

function PayrollView({ token }) {
    const [periodName, setPeriodName] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState('');
    const [success, setSuccess] = React.useState('');

    const handleCalculatePayroll = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');
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
            if (!res.ok) throw new Error(data.msg);
            setSuccess(data.msg);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="payroll-view-container">
            <h3>Cálculo de Planilla</h3>
            <div className="form-section">
                <form onSubmit={handleCalculatePayroll}>
                    <div className="form-group">
                        <label>Nombre del Período (ej. "Planilla Junio 2024")</label>
                        <input
                            type="text"
                            value={periodName}
                            onChange={(e) => setPeriodName(e.target.value)}
                            placeholder="Nombre del Período"
                            required
                        />
                    </div>
                    <button type="submit" disabled={loading}>
                        {loading ? 'Calculando...' : 'Ejecutar Cálculo de Planilla'}
                    </button>
                </form>
                {error && <p style={{ color: 'red' }}>Error: {error}</p>}
                {success && <p style={{ color: 'green' }}>{success}</p>}
            </div>
        </div>
    );
}