function Login({ onLoginSuccess }) {
    const [credentials, setCredentials] = React.useState({
        email: 'contador@test.com', // Default for easy testing
        password: 'password123'
    });
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);

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
            onLoginSuccess(data.access_token);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="login-form">
            <h2>Iniciar Sesión</h2>
            <form onSubmit={handleLogin}>
                <div>
                    <label>Email: </label>
                    <input type="email" name="email" value={credentials.email} onChange={handleInputChange} required />
                </div>
                <div style={{ marginTop: '10px' }}>
                    <label>Contraseña: </label>
                    <input type="password" name="password" value={credentials.password} onChange={handleInputChange} required />
                </div>
                <button type="submit" disabled={isLoading} style={{ marginTop: '10px' }}>
                    {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
                </button>
                {error && <p style={{ color: 'red' }}>{error}</p>}
            </form>
        </div>
    );
}