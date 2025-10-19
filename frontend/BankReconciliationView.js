const BankReconciliationView = ({ token }) => {
    const [file, setFile] = React.useState(null);
    const [statementData, setStatementData] = React.useState({
        account_id: '',
        start_date: '',
        end_date: '',
        start_balance: '',
        end_balance: ''
    });
    const [uploading, setUploading] = React.useState(false);
    const [error, setError] = React.useState('');
    const [statementResult, setStatementResult] = React.useState(null);

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
    };

    const handleInputChange = (event) => {
        const { name, value } = event.target;
        setStatementData(prev => ({ ...prev, [name]: value }));
    };

    const handleUpload = async () => {
        if (!file || !statementData.account_id) {
            setError('Por favor, selecciona una cuenta y un archivo.');
            return;
        }

        setUploading(true);
        setError('');
        const formData = new FormData();
        formData.append('statement', file);
        Object.keys(statementData).forEach(key => {
            formData.append(key, statementData[key]);
        });

        try {
            const response = await fetch(`${API_BASE_URL}/api/reconciliation/upload`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData,
            });

            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || 'Ocurrió un error al subir el archivo.');
            }

            // After successful upload, fetch the processed statement
            fetchStatementDetails(result.statement_id);

        } catch (err) {
            setError(err.message);
        } finally {
            setUploading(false);
        }
    };

    const fetchStatementDetails = async (statementId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/reconciliation/statement/${statementId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudieron cargar los detalles del extracto.');
            const data = await response.json();
            setStatementResult(data);
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div>
            <h3>Conciliación Bancaria (LAN-CB7)</h3>

            {/* Upload Form */}
            <div style={{ border: '1px solid #ccc', padding: '16px', marginBottom: '16px' }}>
                <h4>Subir Extracto Bancario (CSV)</h4>
                <input type="file" onChange={handleFileChange} accept=".csv" />
                <input type="text" name="account_id" value={statementData.account_id} onChange={handleInputChange} placeholder="ID de la Cuenta Contable" />
                <input type="date" name="start_date" value={statementData.start_date} onChange={handleInputChange} />
                <input type="date" name="end_date" value={statementData.end_date} onChange={handleInputChange} />
                <input type="number" name="start_balance" value={statementData.start_balance} onChange={handleInputChange} placeholder="Saldo Inicial" />
                <input type="number" name="end_balance" value={statementData.end_balance} onChange={handleInputChange} placeholder="Saldo Final" />
                <button onClick={handleUpload} disabled={uploading}>
                    {uploading ? 'Procesando...' : 'Subir y Procesar'}
                </button>
                {error && <p style={{ color: 'red' }}>{error}</p>}
            </div>

            {/* Results Display */}
            {statementResult && (
                <div>
                    <h4>Resultados de la Conciliación</h4>
                    <p><strong>Estado:</strong> {statementResult.status}</p>
                    <table>
                        <thead>
                            <tr>
                                <th>Fecha</th>
                                <th>Descripción</th>
                                <th>Monto</th>
                                <th>Tipo</th>
                                <th>Estado Conciliación</th>
                            </tr>
                        </thead>
                        <tbody>
                            {statementResult.transactions.map(tx => (
                                <tr key={tx.id}>
                                    <td>{tx.date}</td>
                                    <td>{tx.description}</td>
                                    <td>{tx.amount.toFixed(2)}</td>
                                    <td>{tx.type}</td>
                                    <td style={{ color: tx.status === 'Reconciled' ? 'green' : 'orange' }}>
                                        {tx.status}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};
