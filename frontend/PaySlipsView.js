const PaySlipsView = ({ token, payrollLogId, onBack }) => {
    const [payslips, setPayslips] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        if (!payrollLogId) return;
        const fetchPaySlips = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/payroll/${payrollLogId}/payslips`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.message || 'No se pudieron cargar los recibos de pago.');
                }
                const data = await response.json();
                setPayslips(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchPaySlips();
    }, [token, payrollLogId]);

    if (loading) return <p>Cargando recibos de pago...</p>;
    if (error) return <p className="error" style={{color: 'red'}}>{error}</p>;

    return (
        <div>
            <h3>Recibos de Pago del Período (ID: {payrollLogId})</h3>
            <button onClick={onBack}>Volver a Nómina</button>
            <table style={{ width: '100%', marginTop: '10px' }}>
                <thead>
                    <tr>
                        <th>Empleado</th>
                        <th>Salario Bruto</th>
                        <th>Deducción ISSS</th>
                        <th>Deducción AFP</th>
                        <th>Deducción Renta</th>
                        <th>Salario Neto</th>
                    </tr>
                </thead>
                <tbody>
                    {payslips.map(slip => (
                        <tr key={slip.id}>
                            <td>{slip.employee_name}</td>
                            <td>${slip.gross_salary.toFixed(2)}</td>
                            <td>${slip.isss_deduction.toFixed(2)}</td>
                            <td>${slip.afp_deduction.toFixed(2)}</td>
                            <td>${slip.renta_deduction.toFixed(2)}</td>
                            <td><strong>${slip.net_salary.toFixed(2)}</strong></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};