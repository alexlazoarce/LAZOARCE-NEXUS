function ContractView({ token, loanId, onBack }) {
    const [contractData, setContractData] = React.useState(null);
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(true);
    const [userRole, setUserRole] = React.useState('');

    const fetchContractData = async () => {
        setError('');
        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/applications/${loanId}/contract-data`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Failed to fetch contract data');
            setContractData(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    React.useEffect(() => {
        if (loanId) {
            fetchContractData();
        }
        // Decode token to get user role
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            setUserRole(payload.role);
        } catch(e) {
            console.error("Failed to decode token", e);
        }
    }, [loanId, token]);

    const handleSignatureAction = async (action) => {
        let url, method = 'POST', body;
        switch(action) {
            case 'request_electronic':
                url = `${API_BASE_URL}/api/applications/${loanId}/request-signature`;
                break;
            case 'upload_manual':
                url = `${API_BASE_URL}/api/applications/${loanId}/upload-signed-document`;
                body = JSON.stringify({ file_url: `/uploads/contrato_${loanId}_firmado.pdf` }); // Simulated URL
                break;
            case 'validate_manual':
                url = `${API_BASE_URL}/api/applications/${loanId}/validate-signature`;
                break;
            default: return;
        }

        try {
            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || `Failed to ${action}`);
            alert(data.message || data.msg || 'Acción completada con éxito.');
            fetchContractData(); // Refresh data to show new status
        } catch (err) {
            setError(err.message);
        }
    };

    const handleDownloadPdf = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/applications/${loanId}/contract.pdf`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error('Failed to download PDF');

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `contrato_${loanId}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

        } catch (err) {
            setError(err.message);
        }
    };

    if (isLoading) return <p>Cargando contrato...</p>;
    if (error) return <p style={{ color: 'red' }}>{error}</p>;
    if (!contractData) return <p>No se encontraron datos del contrato.</p>;

    const { client, loan, company, amortization_table } = contractData;

    const renderSignatureControls = () => {
        const status = loan.signature_status;
        return (
            <div style={{border: '1px solid blue', padding: '1em', margin: '1em 0'}}>
                <h4>Gestión de Firma</h4>
                <p><strong>Estado Actual:</strong> {status}</p>
                {status === 'PENDIENTE' && userRole !== 'Admin' && (
                    <>
                        <button onClick={() => handleSignatureAction('request_electronic')}>Iniciar Firma Electrónica (Simulado)</button>
                        <button onClick={() => handleSignatureAction('upload_manual')} style={{marginLeft: '10px'}}>Subir Documento Firmado (Simulado)</button>
                    </>
                )}
                {status === 'FIRMADO_MANUAL' && userRole === 'Admin' && (
                    <button onClick={() => handleSignatureAction('validate_manual')}>Validar Firma Manual</button>
                )}
                {status === 'VALIDADO' && <p style={{color: 'green'}}>✓ Contrato formalizado y validado.</p>}
                 {status === 'EN_PROCESO_ELECTRONICO' && <p style={{color: 'orange'}}>Esperando firma electrónica del cliente.</p>}
            </div>
        );
    };

    return (
        <div>
            <button onClick={onBack}>&larr; Volver</button>
            <button onClick={handleDownloadPdf} style={{marginLeft: '1em'}}>Descargar PDF Original</button>
            <hr />

            {renderSignatureControls()}

            <div className="contract-preview" style={{border: '1px solid #ccc', padding: '2em', marginTop: '1em'}}>
                <h2 style={{textAlign: 'center'}}>Contrato de Préstamo Simple</h2>
                <p><strong>Deudor:</strong> {client.name} (DUI: {client.dui})</p>
                <p><strong>Monto:</strong> {loan.amount_text}</p>
                 <h3>Tabla de Amortización</h3>
                <table>
                    <thead>
                        <tr><th>Mes</th><th>Cuota</th><th>Principal</th><th>Interés</th><th>Saldo</th></tr>
                    </thead>
                    <tbody>
                        {amortization_table.map(row => (
                            <tr key={row.month}>
                                <td>{row.month}</td>
                                <td>${row.payment.toFixed(2)}</td>
                                <td>${row.principal.toFixed(2)}</td>
                                <td>${row.interest.toFixed(2)}</td>
                                <td>${row.balance.toFixed(2)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}