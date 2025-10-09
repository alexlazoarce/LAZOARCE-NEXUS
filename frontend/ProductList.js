const API_BASE_URL = 'http://127.0.0.1:5000';

function ProductList({ token, onProductSelect }) {
    const [products, setProducts] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchProducts = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/products`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                if (!res.ok) throw new Error('No se pudieron cargar los productos.');
                setProducts(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchProducts();
    }, [token]);

    if (loading) return <p>Cargando productos de crédito...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

    return (
        <div className="product-list-container">
            <h3>Nuestros Productos de Crédito</h3>
            <p>Selecciona un producto para comenzar tu simulación.</p>
            <div className="product-grid">
                {products.length === 0 ? (
                    <p>No hay productos de crédito disponibles en este momento.</p>
                ) : (
                    products.map(product => (
                        <div key={product.id} className="product-card">
                            <h4>{product.name}</h4>
                            <p><strong>Tipo:</strong> {product.loan_type}</p>
                            <p><strong>Monto:</strong> ${product.min_amount.toFixed(2)} - ${product.max_amount.toFixed(2)}</p>
                            <p><strong>Tasa de Interés Mensual:</strong> {product.default_interest_rate}%</p>
                            <button onClick={() => onProductSelect(product)}>
                                Simular y Solicitar
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}