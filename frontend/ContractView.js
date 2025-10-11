const ContractView = ({ token, applicationId, onBack }) => {
    const [contractData, setContractData] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchContractData = async () => {
            if (!applicationId) return;
            try {
                setLoading(true);
                const response = await fetch(`${API_BASE_URL}/api/applications/${applicationId}/contract-data`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.message || 'No se pudieron cargar los datos del contrato.');
                }
                const data = await response.json();
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
    if (error) return <p className="error" style={{ color: 'red' }}>{error}</p>;
    if (!contractData) return null;

    const { application, client, company, amortization_table } = contractData;

    const handleDownloadPdf = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/applications/${applicationId}/contract.pdf`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Error al generar el PDF.');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `contrato_lazo_arce_${applicationId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="contract-container">
            <button onClick={onBack}>Volver a Mis Solicitudes</button>
            <button onClick={handleDownloadPdf} style={{marginLeft: '10px'}}>Descargar PDF</button>

            <h2 style={{textAlign: 'center', marginTop: '20px'}}>CONTRATO DE PRÉSTAMO</h2>

            <p>
                Este Contrato de Préstamo se celebra el {new Date().toLocaleDateString()} entre
                <strong> {company.name}</strong> (en adelante, "el Prestamista") y
                <strong> {client.full_name}</strong> (en adelante, "el Prestatario").
            </p>

            <h4>CLÁUSULAS</h4>
            <ol>
                <li><strong>Monto del Préstamo:</strong> El Prestamista acuerda prestar al Prestatario la suma de ${application.amount_requested.toFixed(2)}.</li>
                <li><strong>Tasa de Interés:</strong> El préstamo devengará un interés anual del {(application.product.interest_rate * 100).toFixed(2)}%.</li>
                <li><strong>Plazo:</strong> El préstamo será reembolsado en {application.term_months} cuotas mensuales.</li>
                <li><strong>Cuota Mensual:</strong> El Prestatario se compromete a pagar una cuota mensual de ${application.monthly_payment.toFixed(2)}.</li>
                <li><strong>Comisiones:</strong> Se aplicará una comisión del {(application.product.commission_rate * 100).toFixed(2)}% mensual, calculada con el método: {application.commission_calculation_method}.</li>
            </ol>

            <h4>TABLA DE AMORTIZACIÓN</h4>
            <table border="1" cellPadding="5" style={{width: '100%', borderCollapse: 'collapse'}}>
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
                    {amortization_table.map(row => (
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

            <div className="signatures" style={{marginTop: '50px', display: 'flex', justifyContent: 'space-around'}}>
                <div>
                    <p>_________________________</p>
                    <p>{company.name}</p>
                    <p>El Prestamista</p>
                </div>
                <div>
                    <p>_________________________</p>
                    <p>{client.full_name}</p>
                    <p>El Prestatario</p>
                </div>
            </div>
        </div>
    );
};