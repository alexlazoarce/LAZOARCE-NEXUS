const API_BASE_URL = 'http://127.0.0.1:5000';

function LoanSimulator({ token, product, onApplicationSuccess }) {
    const [formData, setFormData] = React.useState({
        capital_solicitado: product ? product.min_amount.toString() : '1000',
        meses: '12',
        tasa_interes_mensual: product ? product.default_interest_rate.toString() : '2.5',
        comision_administracion: product ? product.default_admin_commission.toString() : '1',
        comisiones_iniciales: '50',
        commission_method: 'no_interest',
    });
    const [simulationResult, setSimulationResult] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [applying, setApplying] = React.useState(false);
    const [error, setError] = React.useState('');
    const [success, setSuccess] = React.useState('');

    React.useEffect(() => {
        // Pre-cargar datos cuando se selecciona un producto
        if (product) {
            setFormData(prev => ({
                ...prev,
                capital_solicitado: product.min_amount.toString(),
                tasa_interes_mensual: product.default_interest_rate.toString(),
                comision_administracion: product.default_admin_commission.toString(),
            }));
        }
    }, [product]);

    const handleFormChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setSimulationResult(null); // Limpiar simulación anterior al cambiar datos
        setSuccess('');
    };

    const handleSimulate = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');
        setSimulationResult(null);

        try {
            const res = await fetch(`${API_BASE_URL}/api/loans/simulate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg);
            setSimulationResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleApply = async () => {
        setApplying(true);
        setError('');
        setSuccess('');
        try {
            const applicationData = {
                product_id: product.id,
                requested_amount: parseFloat(formData.capital_solicitado),
                requested_term: parseInt(formData.meses, 10),
            };
            const res = await fetch(`${API_BASE_URL}/api/applications`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(applicationData),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg);
            setSuccess(data.msg);
            // Notificar al padre para cambiar de vista
            setTimeout(() => onApplicationSuccess(), 1500);
        } catch (err) {
            setError(err.message);
        } finally {
            setApplying(false);
        }
    };

    if (!product) {
        return <p>Por favor, selecciona un producto de la lista para comenzar.</p>;
    }

    return (
        <div>
            <h3>Simulador para: {product.name}</h3>
            <div className="simulator-container">
                <section className="form-section">
                    <form onSubmit={handleSimulate}>
                        {/* ... campos del formulario ... */}
                        <div className="form-group">
                            <label>Capital Solicitado ($)</label>
                            <input type="number" name="capital_solicitado" value={formData.capital_solicitado} onChange={handleFormChange} min={product.min_amount} max={product.max_amount} required />
                        </div>
                        <div className="form-group">
                            <label>Plazo (Meses)</label>
                            <input type="number" name="meses" value={formData.meses} onChange={handleFormChange} required />
                        </div>
                        {/* ... otros campos ... */}
                        <button type="submit" disabled={loading}>{loading ? 'Calculando...' : 'Calcular Préstamo'}</button>
                    </form>
                </section>
                <section className="results-section">
                    <h3>Resultados de la Simulación</h3>
                    {error && <p style={{color: 'red'}}>{error}</p>}
                    {success && <p style={{color: 'green'}}>{success}</p>}
                    {simulationResult && (
                        <div>
                            {/* ... tabla de amortización ... */}
                            <div className="summary">
                                <h3>Resumen del Préstamo</h3>
                                <p>Total a Pagar: <span>${simulationResult.summary.total_a_pagar.toFixed(2)}</span></p>
                            </div>
                            <button onClick={handleApply} disabled={applying} className="apply-button">
                                {applying ? 'Enviando Solicitud...' : 'Aplicar a este Préstamo'}
                            </button>
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}