function Profile({ token }) {
    const [profile, setProfile] = React.useState({ full_name: '', dui: '', nit: '' });
    const [message, setMessage] = React.useState('');
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(true);

    const fetchProfile = async () => {
        setError('');
        try {
            const res = await fetch(`${API_BASE_URL}/api/profile`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Failed to fetch profile');
            setProfile(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    // Fetch profile on component mount
    React.useEffect(() => {
        fetchProfile();
    }, [token]);

    const handleInputChange = (e) => {
        setProfile({ ...profile, [e.target.name]: e.target.value });
    };

    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(profile)
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Failed to update profile');
            setMessage('Perfil actualizado con éxito.');
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading && !profile.email) {
        return <p>Cargando perfil...</p>;
    }

    return (
        <div>
            <h2>Mi Perfil</h2>
            <p>Esta información se usará para generar sus contratos. Por favor, asegúrese de que sea correcta.</p>
            <form onSubmit={handleUpdateProfile}>
                <div style={{ marginBottom: '10px' }}>
                    <label>Nombre Completo:</label>
                    <input type="text" name="full_name" value={profile.full_name || ''} onChange={handleInputChange} style={{ width: '100%' }} />
                </div>
                <div style={{ marginBottom: '10px' }}>
                    <label>DUI (Documento Único de Identidad):</label>
                    <input type="text" name="dui" value={profile.dui || ''} onChange={handleInputChange} style={{ width: '100%' }} />
                </div>
                <div style={{ marginBottom: '10px' }}>
                    <label>NIT (Número de Identificación Tributaria):</label>
                    <input type="text" name="nit" value={profile.nit || ''} onChange={handleInputChange} style={{ width: '100%' }} />
                </div>
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Guardando...' : 'Guardar Cambios'}
                </button>
                {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
                {message && <p style={{ color: 'green', marginTop: '10px' }}>{message}</p>}
            </form>
        </div>
    );
}