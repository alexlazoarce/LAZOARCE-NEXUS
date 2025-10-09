const API_BASE_URL = 'http://127.0.0.1:5000';

function LoanSimulator({ token }) { // Recibe el token como prop
    const [formData, setFormData] = React.useState({
        capital_solicitado: '1000',
        meses: '12',
        tasa_interes_mensual: '2.5',
        comision_administracion: '1',
        comisiones_iniciales: '50',
        commission_method: 'no_interest',
    });
    const [simulationResult, setSimulationResult] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState('');

    const handleFormChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSimulationResult(null);

        try {
            const res = await fetch(`${API_BASE_URL}/api/loans/simulate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}` // Usa el token recibido por props
                },
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

    return (
        <div className="simulator-container">
            <section className="form-section">
                <h3>Parámetros del Préstamo</h3>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Capital Solicitado ($)</label>
                        <input type="number" name="capital_solicitado" value={formData.capital_solicitado} onChange={handleFormChange} required />
                    </div>
                    <div className="form-group">
                        <label>Plazo (Meses)</label>
                        <input type="number" name="meses" value={formData.meses} onChange={handleFormChange} required />
                    </div>
                    <div className="form-group">
                        <label>Tasa de Interés Mensual (%)</label>
                        <input type="number" step="0.1" name="tasa_interes_mensual" value={formData.tasa_interes_mensual} onChange={handleFormChange} required />
                    </div>
                    <div className="form-group">
                        <label>Comisión de Administración Mensual (%)</label>
                        <input type="number" step="0.1" name="comision_administracion" value={formData.comision_administracion} onChange={handleFormChange} />
                    </div>
                     <div className="form-group">
                        <label>Comisiones Iniciales ($)</label>
                        <input type="number" step="1" name="comisiones_iniciales" value={formData.comisiones_iniciales} onChange={handleFormChange} />
                    </div>
                    <div className="form-group">
                        <label>Método de Comisión</label>
                        <select name="commission_method" value={formData.commission_method} onChange={handleFormChange}>
                            <option value="no_interest">Distribuir en cuotas (sin interés)</option>
                            <option value="add_to_capital">Sumar al capital (genera interés)</option>
                            <option value="subtract_from_capital">Restar del desembolso</option>
                        </select>
                    </div>
                    <button type="submit" disabled={loading}>
                        {loading ? 'Calculando...' : 'Calcular Préstamo'}
                    </button>
                </form>
            </section>
            <section className="results-section">
                <h3>Resultados de la Simulación</h3>
                {error && <p style={{color: 'red'}}>{error}</p>}
                {simulationResult && (
                    <div>
                        <div className="summary">
                            <h3>Resumen del Préstamo</h3>
                            <p>Capital Solicitado: <span>${simulationResult.summary.capital_solicitado.toFixed(2)}</span></p>
                            <p>Monto que recibe el cliente: <span>${simulationResult.summary.capital_recibido_cliente.toFixed(2)}</span></p>
                            <p>Base para cálculo de interés: <span>${simulationResult.summary.base_calculo_intereses.toFixed(2)}</span></p>
                            <p>Total a Pagar: <span>${simulationResult.summary.total_a_pagar.toFixed(2)}</span></p>
                             <p>Total Intereses Pagados: <span>${simulationResult.summary.total_intereses.toFixed(2)}</span></p>
                        </div>
                        <h4>Tabla de Amortización</h4>
                        <table>
                            <thead>
                                <tr>
                                    <th>Mes</th>
                                    <th>Saldo Inicial</th>
                                    <th>Interés</th>
                                    <th>Com. Adm.</th>
                                    <th>Com. Inic.</th>
                                    <th>Amortización</th>
                                    <th>Cuota</th>
                                    <th>Saldo Final</th>
                                </tr>
                            </thead>
                            <tbody>
                                {simulationResult.amortization_table.map((row) => (
                                    <tr key={row.Mes}>
                                        <td>{row.Mes}</td>
                                        <td>${row['Saldo Inicial'].toFixed(2)}</td>
                                        <td>${row['Interés'].toFixed(2)}</td>
                                        <td>${row['Com. Adm'].toFixed(2)}</td>
                                        <td>${row['Com. Inic.'].toFixed(2)}</td>
                                        <td>${row['Amortización'].toFixed(2)}</td>
                                        <td>${row.Cuota.toFixed(2)}</td>
                                        <td>${row['Saldo Final'].toFixed(2)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </div>
    );
}