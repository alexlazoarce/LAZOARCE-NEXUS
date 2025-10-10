function LoanProducts({ onSelectProduct, token }) {
    const [products, setProducts] = React.useState([]);
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(true);

    React.useEffect(() => {
        const fetchProducts = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/loan-products`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.msg || 'Failed to fetch products');
                }
                setProducts(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchProducts();
    }, [token]);

    if (isLoading) {
        return <p>Cargando productos...</p>;
    }

    if (error) {
        return <p style={{ color: 'red' }}>{error}</p>;
    }

    return (
        <div>
            <h2>Productos de Préstamo Disponibles</h2>
            <table>
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Tasa de Interés</th>
                        <th>Plazo (Meses)</th>
                        <th>Monto Mínimo</th>
                        <th>Monto Máximo</th>
                        <th>Acción</th>
                    </tr>
                </thead>
                <tbody>
                    {products.map(product => (
                        <tr key={product.id}>
                            <td>{product.name}</td>
                            <td>{(product.interest_rate * 100).toFixed(2)}%</td>
                            <td>{product.term_months}</td>
                            <td>${product.min_amount.toFixed(2)}</td>
                            <td>${product.max_amount.toFixed(2)}</td>
                            <td>
                                <button onClick={() => onSelectProduct(product)}>
                                    Solicitar
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}