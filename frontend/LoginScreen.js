const API_BASE_URL = 'http://127.0.0.1:5000';

function LoginScreen({ onLoginSuccess }) {
    const [loginData, setLoginData] = React.useState({ email: 'cliente@test.com', password: 'password123' });
    const [authError, setAuthError] = React.useState('');
    const [isRegistering, setIsRegistering] = React.useState(false);

    const handleLoginChange = (e) => {
        setLoginData({ ...loginData, [e.target.name]: e.target.value });
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setIsRegistering(true);
        setAuthError('');
        try {
            const res = await fetch(`${API_BASE_URL}/api/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...loginData, role: 'Cliente' }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg);
            alert('Registro exitoso. Ahora puedes iniciar sesión.');
        } catch (err) {
            setAuthError(err.message);
        } finally {
            setIsRegistering(false);
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setAuthError('');
        try {
            const res = await fetch(`${API_BASE_URL}/api/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(loginData),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg);
            // Si el login es exitoso, llamamos a la función callback del padre
            onLoginSuccess(data.access_token);
        } catch (err) {
            setAuthError(err.message);
        }
    };

    return (
        <div>
            <header>
                <h1>Sistema de Gestión Financiera</h1>
                <h2>Bienvenido</h2>
            </header>
            <main className="login-container">
                <h3>Iniciar Sesión o Registrarse</h3>
                <form>
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input type="email" name="email" value={loginData.email} onChange={handleLoginChange} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">Contraseña</label>
                        <input type="password" name="password" value={loginData.password} onChange={handleLoginChange} />
                    </div>
                    {authError && <p style={{color: 'red'}}>{authError}</p>}
                    <button onClick={handleLogin}>Iniciar Sesión</button>
                    <button onClick={handleRegister} disabled={isRegistering} style={{marginLeft: '10px'}}>
                        {isRegistering ? 'Registrando...' : 'Registrarme'}
                    </button>
                </form>
            </main>
        </div>
    );
}