function LoanProducts({ token, onSelectProduct }) {
    const [products, setProducts] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        fetch(`${API_BASE_URL}/api/loan-products`, { headers: { 'Authorization': `Bearer ${token}` } })
            .then(res => res.ok ? res.json() : Promise.reject(res.json()))
            .then(setProducts)
            .catch(err => err.then(e => setError(e.msg)))
            .finally(() => setIsLoading(false));
    }, [token]);

    if (isLoading) return <p>Cargando productos...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

    return (
        <div>
            <h2>Productos de Préstamo Disponibles</h2>
            <table>
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Tasa de Interés</th>
                        <th>Plazo (Meses)</th>
                        <th>Monto</th>
                        <th>Acción</th>
                    </tr>
                </thead>
                <tbody>
                    {products.map(p => (
                        <tr key={p.id}>
                            <td>{p.name}</td>
                            <td>{(p.interest_rate * 100).toFixed(2)}%</td>
                            <td>{p.term_months}</td>
                            <td>${p.min_amount.toFixed(2)} - ${p.max_amount.toFixed(2)}</td>
                            <td><button onClick={() => onSelectProduct(p)}>Solicitar</button></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}