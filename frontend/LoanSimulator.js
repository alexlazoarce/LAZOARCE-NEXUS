const LoanSimulator = () => {
    const [products, setProducts] = React.useState([]);
    const [selectedProduct, setSelectedProduct] = React.useState('');
    const [amount, setAmount] = React.useState(1000);
    const [term, setTerm] = React.useState(12);
    const [commissionMethod, setCommissionMethod] = React.useState('A');
    const [simulation, setSimulation] = React.useState(null);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchProducts = async () => {
            try {
                // Using a public endpoint for products if available, or the standard one
                const response = await fetch(`${API_BASE_URL}/api/products`);
                if (!response.ok) {
                    throw new Error('No se pudieron cargar los productos');
                }
                const data = await response.json();
                setProducts(data);
                if (data.length > 0) {
                    setSelectedProduct(data[0].id);
                }
            } catch (err) {
                setError(err.message);
            }
        };
        fetchProducts();
    }, []);

    const handleSimulate = async (e) => {
        e.preventDefault();
        setError('');
        setSimulation(null);

        if (!selectedProduct) {
            setError('Por favor, selecciona un producto de préstamo.');
            return;
        }

        try {
            // Using a new public-facing endpoint for simulation
            const response = await fetch(`${API_BASE_URL}/api/public/simulate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_id: parseInt(selectedProduct),
                    amount: parseFloat(amount),
                    term: parseInt(term),
                    commission_calculation_method: commissionMethod,
                }),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Error al simular el préstamo.');
            }
            setSimulation(data);
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div>
            <h3>Simulador de Préstamos</h3>
            <form onSubmit={handleSimulate}>
                <div>
                    <label>Producto de Préstamo:</label>
                    <select value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)}>
                        <option value="">Seleccione un producto</option>
                        {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                </div>
                <div>
                    <label>Monto a Solicitar ($):</label>
                    <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} min="1" required />
                </div>
                <div>
                    <label>Plazo (meses):</label>
                    <input type="number" value={term} onChange={(e) => setTerm(e.target.value)} min="1" required />
                </div>
                <div>
                    <label>Método de Cálculo de Comisión:</label>
                    <select value={commissionMethod} onChange={(e) => setCommissionMethod(e.target.value)}>
                        <option value="A">A) Sobre Saldo de Capital</option>
                        <option value="B">B) Sobre Monto Original</option>
                        <option value="C">C) Cuota Fija</option>
                    </select>
                </div>
                <button type="submit">Simular</button>
            </form>
            {error && <p className="error">{error}</p>}
            {simulation && (
                <div className="simulation-results">
                    <h4>Resultado de la Simulación</h4>
                    <p>Cuota Mensual: ${simulation.monthly_payment.toFixed(2)}</p>
                    <p>Total a Pagar: ${simulation.total_payment.toFixed(2)}</p>
                    <p><strong>Tasa Efectiva Anual (TEA): {(simulation.tea_annual * 100).toFixed(2)}%</strong></p>
                    <h5>Tabla de Amortización:</h5>
                    <table>
                        <thead>
                            <tr>
                                <th>Mes</th>
                                <th>Saldo Inicial</th>
                                <th>Cuota</th>
                                <th>Interés</th>
                                <th>Comisión</th>
                                <th>Amortización</th>
                                <th>Saldo Final</th>
                            </tr>
                        </thead>
                        <tbody>
                            {simulation.amortization_table.map(row => (
                                <tr key={row.month}>
                                    <td>{row.month}</td>
                                    <td>${row.initial_balance.toFixed(2)}</td>
                                    <td>${row.payment.toFixed(2)}</td>
                                    <td>${row.interest.toFixed(2)}</td>
                                    <td>${row.commission.toFixed(2)}</td>
                                    <td>${row.principal.toFixed(2)}</td>
                                    <td>${row.final_balance.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};