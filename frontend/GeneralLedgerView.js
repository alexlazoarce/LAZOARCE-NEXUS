function GeneralLedgerView() {
    const [token, setToken] = React.useState(null);
    const [ledgerData, setLedgerData] = React.useState([]);
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);

    // State for the login form
    const [credentials, setCredentials] = React.useState({
        email: 'contador@test.com',
        password: 'password123'
    });

    const handleInputChange = (e) => {
        setCredentials({ ...credentials, [e.target.name]: e.target.value });
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(credentials),
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.msg || 'Failed to log in');
            }
            setToken(data.access_token);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchLedgerData = async () => {
        if (!token) {
            setError('You must be logged in to fetch data.');
            return;
        }
        setError('');
        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/accounting/general-ledger`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.msg || 'Failed to fetch ledger data');
            }
            setLedgerData(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    if (!token) {
        return (
            <div className="container">
                <h1>Iniciar Sesión para Ver Libro Mayor</h1>
                <form onSubmit={handleLogin} className="login-form">
                    <div>
                        <label>Email: </label>
                        <input type="email" name="email" value={credentials.email} onChange={handleInputChange} />
                    </div>
                    <div style={{marginTop: '10px'}}>
                        <label>Contraseña: </label>
                        <input type="password" name="password" value={credentials.password} onChange={handleInputChange} />
                    </div>
                    <button type="submit" disabled={isLoading} style={{marginTop: '10px'}}>
                        {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
                    </button>
                    {error && <p style={{color: 'red'}}>{error}</p>}
                </form>
            </div>
        );
    }

    return (
        <div className="container">
            <h1>Libro Mayor General</h1>
            <div className="ledger-view">
                <button onClick={fetchLedgerData} disabled={isLoading}>
                    {isLoading ? 'Cargando...' : 'Cargar Libro Mayor'}
                </button>
                {error && <p style={{color: 'red'}}>{error}</p>}
                {ledgerData.length > 0 && (
                    <table>
                        <thead>
                            <tr>
                                <th>Código</th>
                                <th>Nombre de Cuenta</th>
                                <th>Total Débitos</th>
                                <th>Total Créditos</th>
                                <th>Saldo Final</th>
                            </tr>
                        </thead>
                        <tbody>
                            {ledgerData.map(acc => (
                                <tr key={acc.account_code}>
                                    <td>{acc.account_code}</td>
                                    <td>{acc.account_name}</td>
                                    <td>${acc.total_debits.toFixed(2)}</td>
                                    <td>${acc.total_credits.toFixed(2)}</td>
                                    <td>${acc.final_balance.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}