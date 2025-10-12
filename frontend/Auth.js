const Auth = ({ onLogin }) => {
    const [email, setEmail] = React.useState('');
    const [password, setPassword] = React.useState('');
    const [tenantName, setTenantName] = React.useState('');
    const [error, setError] = React.useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');

        // Special case for SuperAdmin login
        const effectiveTenantName = email === 'support@lazoarce.com' ? 'LAZOARCE NEXUS' : tenantName;

        if (!effectiveTenantName) {
            setError('Por favor, ingrese el nombre de la empresa.');
            return;
        }

        const url = `${API_BASE_URL}/api/auth/login`;
        const payload = { email, password, tenant_name: effectiveTenantName };

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Error en la autenticación');
            }

            if (data.access_token) {
                onLogin(data.access_token);
            } else {
                throw new Error('No se recibió el token de acceso');
            }
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="auth-container">
            <h2>Iniciar Sesión</h2>
            <form onSubmit={handleLogin}>
                {email !== 'support@lazoarce.com' && (
                     <div>
                        <label htmlFor="tenantName">Nombre de la Empresa (Inquilino):</label>
                        <input
                            id="tenantName"
                            type="text"
                            value={tenantName}
                            onChange={(e) => setTenantName(e.target.value)}
                            required
                            placeholder="Ej: Mi Empresa"
                            data-testid="tenant-name-input"
                        />
                    </div>
                )}
                <div>
                    <label htmlFor="email">Email:</label>
                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        placeholder="usuario@ejemplo.com"
                    />
                </div>
                <div>
                    <label htmlFor="password">Contraseña:</label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                {error && <p className="error" style={{color: 'red'}}>{error}</p>}
                <button type="submit">Iniciar Sesión</button>
            </form>
            <p style={{marginTop: '20px', fontSize: '0.8em', color: 'grey'}}>
                El registro de nuevos usuarios es gestionado por el administrador de su empresa.
            </p>
        </div>
    );
};