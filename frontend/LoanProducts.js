const LoanProducts = ({ token }) => {
    const [products, setProducts] = React.useState([]);
    const [error, setError] = React.useState('');
    const [userRoles, setUserRoles] = React.useState([]);

    // States for the new product form
    const [name, setName] = React.useState('');
    const [minAmount, setMinAmount] = React.useState('');
    const [maxAmount, setMaxAmount] = React.useState('');
    const [interestRate, setInterestRate] = React.useState('');
    const [commissionRate, setCommissionRate] = React.useState('');
    const [term, setTerm] = React.useState('');


    const fetchProducts = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/products`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('Error al cargar productos');
            const data = await response.json();
            setProducts(data);
        } catch (err) {
            setError(err.message);
        }
    };

    const fetchProfile = async () => {
         try {
            const response = await fetch(`${API_BASE_URL}/api/profile`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('Error al cargar perfil');
            const data = await response.json();
            setUserRoles(data.roles || []);
        } catch (err) {
            setError(err.message);
        }
    };


    React.useEffect(() => {
        if (token) {
            fetchProducts();
            fetchProfile();
        }
    }, [token]);

    const isAdmin = userRoles.includes('Admin');

    const handleAddProduct = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/products`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name,
                    min_amount: parseFloat(minAmount),
                    max_amount: parseFloat(maxAmount),
                    interest_rate: parseFloat(interestRate) / 100, // Convert to decimal
                    commission_rate: parseFloat(commissionRate) / 100, // Convert to decimal
                    term: parseInt(term)
                }),
            });
            if (!response.ok) {
                 const errData = await response.json();
                 throw new Error(errData.message || 'No se pudo crear el producto.');
            }
            // Reset form and refresh list
            setName('');
            setMinAmount('');
            setMaxAmount('');
            setInterestRate('');
            setCommissionRate('');
            setTerm('');
            fetchProducts();
        } catch (err) {
            setError(err.message);
        }
    };


    return (
        <div>
            <h3>Productos de Préstamo Disponibles</h3>
            {error && <p className="error">{error}</p>}
            <ul>
                {products.map(p => (
                    <li key={p.id}>
                        <strong>{p.name}</strong> - Monto: ${p.min_amount} a ${p.max_amount} | Plazo: {p.term} meses | Tasa Interés: {(p.interest_rate * 100).toFixed(2)}% | Tasa Comisión: {(p.commission_rate * 100).toFixed(2)}%
                    </li>
                ))}
            </ul>

            {isAdmin && (
                 <div>
                    <h4>Agregar Nuevo Producto</h4>
                    <form onSubmit={handleAddProduct}>
                        <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Nombre del Producto" required />
                        <input type="number" value={minAmount} onChange={e => setMinAmount(e.target.value)} placeholder="Monto Mínimo" required />
                        <input type="number" value={maxAmount} onChange={e => setMaxAmount(e.target.value)} placeholder="Monto Máximo" required />
                        <input type="number" value={interestRate} onChange={e => setInterestRate(e.target.value)} placeholder="Tasa de Interés Anual (%)" required step="0.01" />
                        <input type="number" value={commissionRate} onChange={e => setCommissionRate(e.target.value)} placeholder="Tasa de Comisión Mensual (%)" required step="0.01" />
                        <input type="number" value={term} onChange={e => setTerm(e.target.value)} placeholder="Plazo Máximo (meses)" required />
                        <button type="submit">Agregar Producto</button>
                    </form>
                </div>
            )}
        </div>
    );
};