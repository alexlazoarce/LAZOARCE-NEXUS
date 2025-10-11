function ContractView({ token, loanId, onBack }) {
    const [contractData, setContractData] = React.useState(null);
    const [isLoading, setIsLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [userRole, setUserRole] = React.useState('');

    const fetchContractData = () => {
        setIsLoading(true);
        fetch(`${API_BASE_URL}/api/loan-applications/${loanId}/contract-data`, { headers: { 'Authorization': `Bearer ${token}` } })
            .then(res => res.ok ? res.json() : Promise.reject(res.json()))
            .then(setContractData)
            .catch(err => err.then(e => setError(e.msg)))
            .finally(() => setIsLoading(false));
    };

    React.useEffect(() => {
        fetchContractData();
        try {
            setUserRole(JSON.parse(atob(token.split('.')[1])).role);
        } catch (e) { console.error(e); }
    }, [loanId, token]);

    const handleSignatureAction = async (action) => {
        const actions = {
            'request_electronic': { url: `${API_BASE_URL}/api/loan-applications/${loanId}/request-signature`, method: 'POST', body: null },
            'upload_manual': { url: `${API_BASE_URL}/api/loan-applications/${loanId}/upload-signed-document`, method: 'POST', body: JSON.stringify({ file_url: `/uploads/contrato_${loanId}_firmado.pdf` }) },
            'validate_manual': { url: `${API_BASE_URL}/api/loan-applications/${loanId}/validate-signature`, method: 'POST', body: null }
        };
        const { url, method, body } = actions[action];
        try {
            const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Error en la acción');
            alert(data.message || data.msg || 'Acción completada');
            fetchContractData();
        } catch (err) {
            setError(err.message);
        }
    };

    const handleDownloadPdf = () => { /* ... download logic ... */ };

    if (isLoading) return <p>Cargando contrato...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
    if (!contractData) return <p>No hay datos de contrato.</p>;

    const { client, loan, company, amortization_table } = contractData;

    return (
        <div>
            <button onClick={onBack}>&larr; Volver</button>
            <button onClick={handleDownloadPdf}>Descargar PDF</button>
            <div style={{border: '1px solid blue', padding: '1em', margin: '1em 0'}}>
                <h4>Gestión de Firma</h4>
                <p><strong>Estado:</strong> {loan.signature_status}</p>
                {loan.signature_status === 'PENDIENTE' && userRole !== 'Admin' && <button onClick={() => handleSignatureAction('upload_manual')}>Subir Documento Firmado</button>}
                {loan.signature_status === 'FIRMADO_MANUAL' && userRole === 'Admin' && <button onClick={() => handleSignatureAction('validate_manual')}>Validar Firma</button>}
                {loan.signature_status === 'VALIDADO' && <p>✓ Contrato Validado</p>}
            </div>
            <div className="contract-preview">
                <h2>Contrato de Préstamo</h2>
                <p><strong>Deudor:</strong> {client.name} (DUI: {client.dui})</p>
                {/* ... more contract details ... */}
            </div>
        </div>
    );
}