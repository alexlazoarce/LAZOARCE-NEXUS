function Login({ onLoginSuccess }) {
    const [credentials, setCredentials] = React.useState({ email: '', password: '' });
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);

    const handleInputChange = (e) => setCredentials({ ...credentials, [e.target.name]: e.target.value });

    const handleLogin = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        try {
            const res = await fetch(`${API_BASE_URL}/api/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(credentials),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Error de autenticación');
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
                <input name="email" type="email" value={credentials.email} onChange={handleInputChange} placeholder="Email" required />
                <input name="password" type="password" value={credentials.password} onChange={handleInputChange} placeholder="Contraseña" required />
                <button type="submit" disabled={isLoading}>{isLoading ? 'Iniciando...' : 'Iniciar Sesión'}</button>
                {error && <p style={{ color: 'red' }}>{error}</p>}
            </form>
        </div>
    );
}