function LoanDetailView({ token, loanId, onBack }) {
    const [details, setDetails] = React.useState(null);
    const [isLoading, setIsLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [paymentAmount, setPaymentAmount] = React.useState('');

    const fetchDetails = () => {
        setIsLoading(true);
        fetch(`${API_BASE_URL}/api/loan-applications/${loanId}/amortization`, { headers: { 'Authorization': `Bearer ${token}` } })
            .then(res => res.ok ? res.json() : Promise.reject(res.json()))
            .then(setDetails)
            .catch(err => err.then(e => setError(e.msg)))
            .finally(() => setIsLoading(false));
    };

    React.useEffect(fetchDetails, [loanId, token]);

    const handleRecordPayment = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch(`${API_BASE_URL}/api/loan-applications/${loanId}/payments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ amount: parseFloat(paymentAmount) }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Error al registrar el pago');
            alert('Pago registrado con éxito!');
            setPaymentAmount('');
            fetchDetails();
        } catch (err) {
            setError(err.message);
        }
    };

    if (isLoading) return <p>Cargando detalles del préstamo...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
    if (!details) return <p>No hay detalles para mostrar.</p>;

    return (
        <div>
            <button onClick={onBack}>&larr; Volver</button>
            <h2>Detalles del Préstamo (ID: {loanId})</h2>
            <form onSubmit={handleRecordPayment}><input type="number" value={paymentAmount} onChange={e => setPaymentAmount(e.target.value)} placeholder="Monto del pago" /><button type="submit">Registrar Pago</button></form>
            <h3>Historial de Pagos</h3>
            <table><thead><tr><th>Fecha</th><th>Monto</th></tr></thead><tbody>{details.payments.map((p, i) => <tr key={i}><td>{new Date(p.date).toLocaleString()}</td><td>${p.amount.toFixed(2)}</td></tr>)}</tbody></table>
            <h3>Tabla de Amortización</h3>
            <table><thead><tr><th>Mes</th><th>Cuota</th><th>Principal</th><th>Interés</th><th>Saldo</th></tr></thead><tbody>{details.schedule.map(row => <tr key={row.month}><td>{row.month}</td><td>${row.payment.toFixed(2)}</td><td>${row.principal.toFixed(2)}</td><td>${row.interest.toFixed(2)}</td><td>${row.balance.toFixed(2)}</td></tr>)}</tbody></table>
        </div>
    );
}