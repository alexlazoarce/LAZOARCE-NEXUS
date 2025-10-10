function LoanDetailView({ token, loanId, onBack }) {
    const [details, setDetails] = React.useState({ schedule: [], summary: {}, payments: [] });
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(true);
    const [paymentAmount, setPaymentAmount] = React.useState('');

    const fetchDetails = async () => {
        setIsLoading(true);
        setError('');
        try {
            const res = await fetch(`${API_BASE_URL}/api/loan-applications/${loanId}/amortization`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Failed to fetch loan details');
            setDetails(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    React.useEffect(() => {
        if (loanId) {
            fetchDetails();
        }
    }, [loanId, token]);

    const handleRecordPayment = async (e) => {
        e.preventDefault();
        setError('');
        if (!paymentAmount || parseFloat(paymentAmount) <= 0) {
            setError('Please enter a valid payment amount.');
            return;
        }

        try {
            const res = await fetch(`${API_BASE_URL}/api/loan-applications/${loanId}/payments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ amount: parseFloat(paymentAmount) }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Failed to record payment');

            alert('Payment recorded successfully!');
            setPaymentAmount(''); // Clear input
            fetchDetails(); // Refresh details to show new payment
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div>
            <button onClick={onBack}>&larr; Volver a Mis Solicitudes</button>
            <h2>Detalles del Préstamo (ID: {loanId})</h2>
            {isLoading && <p>Cargando detalles...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}

            {/* Payment Form */}
            <div className="payment-form">
                <h3>Registrar Pago</h3>
                <form onSubmit={handleRecordPayment}>
                    <input
                        type="number"
                        value={paymentAmount}
                        onChange={(e) => setPaymentAmount(e.target.value)}
                        placeholder="Monto del pago"
                        step="0.01"
                    />
                    <button type="submit">Registrar Pago</button>
                </form>
            </div>

            {/* Payment History */}
            <h3>Historial de Pagos</h3>
            {details.payments && details.payments.length > 0 ? (
                <table>
                    <thead><tr><th>Fecha</th><th>Monto</th></tr></thead>
                    <tbody>
                        {details.payments.map((p, i) => <tr key={i}><td>{new Date(p.date).toLocaleString()}</td><td>${p.amount.toFixed(2)}</td></tr>)}
                    </tbody>
                </table>
            ) : <p>No se han registrado pagos.</p>}

            {/* Amortization Schedule */}
            <h3>Tabla de Amortización</h3>
            {details.schedule && details.schedule.length > 0 ? (
                <table>
                    <thead>
                        <tr><th>Mes</th><th>Cuota</th><th>Principal</th><th>Interés</th><th>Saldo</th></tr>
                    </thead>
                    <tbody>
                        {details.schedule.map(row => (
                            <tr key={row.month}>
                                <td>{row.month}</td>
                                <td>${row.payment.toFixed(2)}</td>
                                <td>${row.principal.toFixed(2)}</td>
                                <td>${row.interest.toFixed(2)}</td>
                                <td>${row.balance.toFixed(2)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : <p>No se pudo generar la tabla de amortización.</p>}
        </div>
    );
}