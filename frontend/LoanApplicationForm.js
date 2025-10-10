function LoanApplicationForm({ product, onApplicationSuccess, token }) {
    const [formData, setFormData] = React.useState({
        requested_amount: product.min_amount,
        requested_term: product.term_months
    });
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        // Basic validation
        if (formData.requested_amount < product.min_amount || formData.requested_amount > product.max_amount) {
            setError(`El monto debe estar entre $${product.min_amount} y $${product.max_amount}.`);
            setIsLoading(false);
            return;
        }

        try {
            const res = await fetch(`${API_BASE_URL}/api/loan-applications`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    ...formData,
                    product_id: product.id
                }),
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.msg || 'Error al enviar la solicitud');
            }
            alert('¡Solicitud enviada con éxito!');
            onApplicationSuccess(); // Callback to parent to change view
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            <h2>Solicitar Préstamo: {product.name}</h2>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Monto a Solicitar: </label>
                    <input
                        type="number"
                        name="requested_amount"
                        value={formData.requested_amount}
                        onChange={handleInputChange}
                        min={product.min_amount}
                        max={product.max_amount}
                        required
                    />
                </div>
                <div style={{ marginTop: '10px' }}>
                    <label>Plazo (meses): </label>
                    <input
                        type="number"
                        name="requested_term"
                        value={formData.requested_term}
                        onChange={handleInputChange}
                        required
                    />
                </div>
                <button type="submit" disabled={isLoading} style={{ marginTop: '10px' }}>
                    {isLoading ? 'Enviando...' : 'Enviar Solicitud'}
                </button>
                {error && <p style={{ color: 'red' }}>{error}</p>}
            </form>
        </div>
    );
}