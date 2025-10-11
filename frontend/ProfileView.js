const ProfileView = ({ token }) => {
    const [profile, setProfile] = React.useState({ full_name: '', dui: '', nit: '', email: '' });
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [message, setMessage] = React.useState('');

    React.useEffect(() => {
        const fetchProfile = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/profile`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) throw new Error('No se pudo cargar el perfil.');
                const data = await response.json();
                setProfile(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, [token]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setProfile(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(profile),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Error al actualizar el perfil.');
            setMessage('¡Perfil actualizado con éxito!');
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) return <p>Cargando perfil...</p>;

    return (
        <div>
            <h3>Mi Perfil</h3>
            <p>Completa tu información para poder solicitar préstamos.</p>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Nombre Completo:</label>
                    <input type="text" name="full_name" value={profile.full_name || ''} onChange={handleInputChange} required />
                </div>
                <div>
                    <label>DUI (Documento Único de Identidad):</label>
                    <input type="text" name="dui" value={profile.dui || ''} onChange={handleInputChange} required />
                </div>
                <div>
                    <label>NIT (Número de Identificación Tributaria):</label>
                    <input type="text" name="nit" value={profile.nit || ''} onChange={handleInputChange} required />
                </div>
                <div>
                    <label>Email:</label>
                    <input type="email" name="email" value={profile.email || ''} disabled />
                </div>
                <button type="submit">Guardar Cambios</button>
            </form>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {message && <p style={{ color: 'green' }}>{message}</p>}
        </div>
    );
};