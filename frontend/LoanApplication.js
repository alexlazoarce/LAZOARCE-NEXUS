const LoanApplication = ({ token, onNavigate }) => {
    const [products, setProducts] = React.useState([]);
    const [profile, setProfile] = React.useState(null);
    const [loading, setLoading] = React.useState(true);

    const [selectedProduct, setSelectedProduct] = React.useState('');
    const [amount, setAmount] = React.useState('');
    const [term, setTerm] = React.useState('');
    const [commissionMethod, setCommissionMethod] = React.useState('A');

    const [error, setError] = React.useState('');
    const [message, setMessage] = React.useState('');

    React.useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch both profile and products
                const [profileRes, productsRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/api/profile`, { headers: { 'Authorization': `Bearer ${token}` } }),
                    fetch(`${API_BASE_URL}/api/products`, { headers: { 'Authorization': `Bearer ${token}` } })
                ]);

                if (!profileRes.ok) throw new Error('No se pudo cargar tu perfil.');
                if (!productsRes.ok) throw new Error('No se pudieron cargar los productos.');

                const profileData = await profileRes.json();
                const productsData = await productsRes.json();

                setProfile(profileData);
                setProducts(productsData);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [token]);

    const handleProductChange = (e) => {
        const productId = e.target.value;
        setSelectedProduct(productId);
        const product = products.find(p => p.id === parseInt(productId));
        if (product) {
            // Automatically set the term and a default amount
            setTerm(product.term_months);
            setAmount(product.min_amount);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');

        if (!selectedProduct) {
            setError('Debe seleccionar un producto de préstamo.');
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/loan_applications`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    product_id: parseInt(selectedProduct),
                    amount_requested: parseFloat(amount),
                    term_months: parseInt(term),
                    commission_calculation_method: commissionMethod,
                }),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Ocurrió un error al enviar la solicitud.');
            }

            setMessage('¡Solicitud enviada con éxito! Puede ver el estado en "Mis Solicitudes".');
            // Reset form
            setSelectedProduct('');
            setAmount('');
            setTerm('');
        } catch (err) {
            setError(err.message);
        }
    };

    const productDetails = products.find(p => p.id === parseInt(selectedProduct));

    if (loading) {
        return <p>Cargando...</p>;
    }

    const isProfileComplete = profile && profile.full_name && profile.dui && profile.nit;

    if (!isProfileComplete) {
        return (
            <div>
                <h3>Perfil Incompleto</h3>
                <p>Para poder solicitar un préstamo, primero debe completar su información personal en su perfil.</p>
                <p>Por favor, asegúrese de haber ingresado su Nombre Completo, DUI y NIT.</p>
                {/* This button will require onNavigate prop from App.js */}
                <button onClick={() => onNavigate('profile')}>Ir a Mi Perfil</button>
            </div>
        );
    }

    return (
        <div>
            <h3>Nueva Solicitud de Préstamo</h3>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Seleccione un Producto:</label>
                    <select value={selectedProduct} onChange={handleProductChange} required>
                        <option value="">-- Elija un producto --</option>
                        {products.map(p => (
                            <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                    </select>
                </div>

                {productDetails && (
                    <>
                        <div>
                            <label>Monto a Solicitar (${productDetails.min_amount} - ${productDetails.max_amount}):</label>
                            <input
                                type="number"
                                value={amount}
                                onChange={e => setAmount(e.target.value)}
                                min={productDetails.min_amount}
                                max={productDetails.max_amount}
                                required
                            />
                        </div>
                        <div>
                            <label>Plazo (meses):</label>
                            <input
                                type="number"
                                value={term}
                                onChange={e => setTerm(e.target.value)}
                                max={productDetails.term_months}
                                required
                            />
                        </div>
                        <div>
                            <label>Método de Comisión:</label>
                            <select value={commissionMethod} onChange={e => setCommissionMethod(e.target.value)}>
                                <option value="A">Sobre Saldo de Capital</option>
                                <option value="B">Sobre Monto Original</option>
                                <option value="C">Cuota Fija</option>
                            </select>
                        </div>
                    </>
                )}

                <button type="submit" disabled={!selectedProduct}>Enviar Solicitud</button>
            </form>
            {error && <p className="error" style={{color: 'red'}}>{error}</p>}
            {message && <p className="message" style={{color: 'green'}}>{message}</p>}
        </div>
    );
};