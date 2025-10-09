const API_BASE_URL = 'http://127.0.0.1:5000';

function ContractView({ token, applicationId, onBack }) {
    const [contractData, setContractData] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [downloading, setDownloading] = React.useState(false);

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

    const handleDownload = async () => {
        setDownloading(true);
        setError('');
        try {
            const res = await fetch(`${API_BASE_URL}/api/applications/${applicationId}/contract.pdf`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error('No se pudo descargar el PDF.');

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `contrato_${applicationId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

        } catch (err) {
            setError(err.message);
        } finally {
            setDownloading(false);
        }
    };

    if (loading) return <p>Cargando contrato...</p>;
    if (error) return <p style={{color: 'red'}}>Error: {error}</p>;
    if (!contractData) return <p>No se encontraron datos del contrato.</p>;

    const { company, client, loan, amortization } = contractData;

    return (
        <div className="contract-container">
            <div className="contract-actions">
                <button onClick={onBack} className="back-button">← Volver a Mis Solicitudes</button>
                <button onClick={handleDownload} disabled={downloading} className="download-button">
                    {downloading ? 'Descargando...' : 'Descargar Contrato en PDF'}
                </button>
            </div>
            <header className="contract-header">
                <h2>CONTRATO DE PRÉSTAMO DE DINERO</h2>
                <div>
                    <p><strong>{company.name}</strong></p>
                    <p>NIT: {company.nit} | NRC: {company.nrc}</p>
                </div>
            </header>
            {/* ... resto del contrato ... */}
            <section>
                <h3>PLAN DE PAGOS</h3>
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
        </div>
    );
}