function ContractView({ token, loanId, onBack }) {
    const [contractData, setContractData] = React.useState(null);
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(true);

    React.useEffect(() => {
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

        if (loanId) {
            fetchContractData();
        }
    }, [loanId, token]);

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

    if (isLoading) {
        return <p>Cargando contrato...</p>;
    }

    if (error) {
        return <p style={{ color: 'red' }}>{error}</p>;
    }

    if (!contractData) {
        return <p>No se encontraron datos del contrato.</p>;
    }

    const { client, loan, company, amortization_table } = contractData;

    return (
        <div>
            <button onClick={onBack}>&larr; Volver</button>
            <button onClick={handleDownloadPdf} style={{marginLeft: '1em'}}>Descargar PDF</button>
            <hr />
            <div className="contract-preview" style={{border: '1px solid #ccc', padding: '2em', marginTop: '1em'}}>
                <h2 style={{textAlign: 'center'}}>Contrato de Préstamo Simple</h2>
                <p>
                    <strong>Fecha:</strong> {new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })}
                </p>

                <h3>Partes Involucradas</h3>
                <p>
                    <strong>Acreedor:</strong> {company.name} (NIT: {company.nit}), representado por {company.legal_rep}.
                </p>
                <p>
                    <strong>Deudor:</strong> {client.name} (DUI: {client.dui}, NIT: {client.nit}).
                </p>

                <h3>Términos del Préstamo</h3>
                <p>
                    Por el presente, el Acreedor acuerda prestar al Deudor la suma de <strong>{loan.amount_text}</strong>.
                    El préstamo se regirá por los siguientes términos:
                </p>
                <ul>
                    <li><strong>Producto:</strong> {loan.product_name}</li>
                    <li><strong>Plazo:</strong> {loan.term_months} meses</li>
                    <li><strong>Tasa de Interés Anual:</strong> {loan.interest_rate_annual}</li>
                    <li><strong>Cuota Mensual Fija:</strong> {loan.monthly_payment}</li>
                </ul>

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

                <div style={{marginTop: '40px', display: 'flex', justifyContent: 'space-around'}}>
                    <div>
                        <p>_________________________</p>
                        <p style={{textAlign: 'center'}}>{client.name}<br/>(Deudor)</p>
                    </div>
                    <div>
                        <p>_________________________</p>
                        <p style={{textAlign: 'center'}}>{company.name}<br/>(Acreedor)</p>
                    </div>
                </div>
            </div>
        </div>
    );
}