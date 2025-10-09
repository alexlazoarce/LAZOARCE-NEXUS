const API_BASE_URL = 'http://127.0.0.1:5000';

function ContractView({ token, applicationId, onBack }) {
    const [contractData, setContractData] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        if (!applicationId) return;

        const fetchContractData = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/applications/${applicationId}/contract-data`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.msg);
                setContractData(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchContractData();
    }, [token, applicationId]);

    if (loading) return <p>Cargando contrato...</p>;
    if (error) return <p style={{color: 'red'}}>Error: {error}</p>;
    if (!contractData) return <p>No se encontraron datos del contrato.</p>;

    const { company, client, loan, amortization } = contractData;

    return (
        <div className="contract-container">
            <button onClick={onBack} className="back-button">← Volver a Mis Solicitudes</button>
            <header className="contract-header">
                <h2>CONTRATO DE PRÉSTAMO DE DINERO</h2>
                <div>
                    <p><strong>{company.name}</strong></p>
                    <p>NIT: {company.nit} | NRC: {company.nrc}</p>
                </div>
            </header>

            <section>
                <h3>PARTES DEL CONTRATO</h3>
                <p><strong>DEUDOR:</strong> {client.full_name}, con DUI: {client.dui} y NIT: {client.nit}.</p>
                <p><strong>ACREEDOR:</strong> {company.name}.</p>
            </section>

            <section>
                <h3>DETALLES DEL PRÉSTAMO</h3>
                <p><strong>Monto del Préstamo:</strong> ${loan.requested_amount.toFixed(2)}</p>
                <p><strong>Plazo:</strong> {loan.requested_term} meses</p>
                <p><strong>Tasa de Interés Mensual:</strong> {loan.interest_rate}%</p>
                <p><strong>Fecha de Solicitud:</strong> {new Date(loan.application_date).toLocaleDateString()}</p>
            </section>

            <section>
                <h3>PLAN DE PAGOS</h3>
                <p>El DEUDOR se compromete a pagar al ACREEDOR según la siguiente tabla de amortización:</p>
                <div className="results-section">
                    <table>
                        <thead>
                            <tr>
                                <th>Mes</th>
                                <th>Fecha Vencimiento</th>
                                <th>Saldo Inicial</th>
                                <th>Interés</th>
                                <th>Com. Adm.</th>
                                <th>Amortización</th>
                                <th>Cuota</th>
                                <th>Saldo Final</th>
                            </tr>
                        </thead>
                        <tbody>
                            {amortization.amortization_table.map((row) => (
                                <tr key={row.Mes}>
                                    <td>{row.Mes}</td>
                                    <td>{row['Fecha Vencimiento']}</td>
                                    <td>${row['Saldo Inicial'].toFixed(2)}</td>
                                    <td>${row['Interés'].toFixed(2)}</td>
                                    <td>${row['Com. Adm'].toFixed(2)}</td>
                                    <td>${row['Amortización'].toFixed(2)}</td>
                                    <td>${row.Cuota.toFixed(2)}</td>
                                    <td>${row['Saldo Final'].toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            <footer className="contract-footer">
                <p>Firmado electrónicamente el {new Date().toLocaleDateString()}.</p>
            </footer>
        </div>
    );
}