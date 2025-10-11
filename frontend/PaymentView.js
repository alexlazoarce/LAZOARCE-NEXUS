const PaymentView = ({ token, application, onBack }) => {
    const [payments, setPayments] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    // Form state for new payment
    const [amountPaid, setAmountPaid] = React.useState('');
    const [paymentDate, setPaymentDate] = React.useState(new Date().toISOString().split('T')[0]);

    const fetchPayments = async () => {
        // In a real app, you'd fetch payments for the application.
        // For now, we assume payments are part of the application object or would be fetched separately.
        // This part is simplified for now.
        setLoading(false);
    };

    React.useEffect(() => {
        fetchPayments();
    }, [application.id]);

    const handleAddPayment = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/applications/${application.id}/payments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    amount_paid: parseFloat(amountPaid),
                    payment_date: paymentDate,
                    type: 'Cuota' // Or other types
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Error al registrar el pago.');

            // For now, just alert and clear form. A real app would refresh the payment list.
            alert('¡Pago registrado con éxito!');
            setAmountPaid('');
            // You would typically refetch payments here.
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) return <p>Cargando pagos...</p>;

    return (
        <div>
            <button onClick={onBack}>Volver al Panel</button>
            <h3>Registrar Pago para Préstamo #{application.id}</h3>
            <p><strong>Cliente:</strong> {application.applicant_name}</p>
            <p><strong>Monto del Préstamo:</strong> ${application.amount_requested.toFixed(2)}</p>
            <p><strong>Estado:</strong> {application.status}</p>

            <hr />

            <h4>Registrar Nuevo Pago</h4>
            <form onSubmit={handleAddPayment}>
                <input
                    type="number"
                    value={amountPaid}
                    onChange={e => setAmountPaid(e.target.value)}
                    placeholder="Monto a Pagar"
                    required
                    step="0.01"
                />
                <input
                    type="date"
                    value={paymentDate}
                    onChange={e => setPaymentDate(e.target.value)}
                    required
                />
                <button type="submit">Registrar Pago</button>
            </form>
            {error && <p style={{color: 'red'}}>{error}</p>}

            <hr />
            <h4>Historial de Pagos (Simplificado)</h4>
            {/* A full implementation would fetch and display payments here */}
            <p>El historial de pagos se mostrará aquí en una futura iteración.</p>
        </div>
    );
};