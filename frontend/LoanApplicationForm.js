function LoanApplicationForm({ token, product, onApplicationSuccess }) {
    const [formData, setFormData] = React.useState({
        requested_amount: product.min_amount,
        requested_term: product.term_months
    });
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);

    const handleInputChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        try {
            const res = await fetch(`${API_BASE_URL}/api/loan-applications`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ ...formData, product_id: product.id }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Error al enviar la solicitud');
            alert('¡Solicitud enviada con éxito!');
            onApplicationSuccess();
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
                <input type="number" name="requested_amount" value={formData.requested_amount} onChange={handleInputChange} min={product.min_amount} max={product.max_amount} required />
                <input type="number" name="requested_term" value={formData.requested_term} onChange={handleInputChange} required />
                <button type="submit" disabled={isLoading}>{isLoading ? 'Enviando...' : 'Enviar Solicitud'}</button>
                {error && <p style={{ color: 'red' }}>{error}</p>}
            </form>
        </div>
    );
}