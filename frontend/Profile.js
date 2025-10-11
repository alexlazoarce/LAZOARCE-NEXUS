function Profile({ token }) {
    const [profile, setProfile] = React.useState({ full_name: '', dui: '', nit: '' });
    const [message, setMessage] = React.useState('');
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(true);

    const fetchProfile = () => {
        setIsLoading(true);
        fetch(`${API_BASE_URL}/api/profile`, { headers: { 'Authorization': `Bearer ${token}` } })
            .then(res => res.ok ? res.json() : Promise.reject(res.json()))
            .then(setProfile)
            .catch(err => err.then(e => setError(e.msg)))
            .finally(() => setIsLoading(false));
    };

    React.useEffect(fetchProfile, [token]);

    const handleInputChange = (e) => setProfile({ ...profile, [e.target.name]: e.target.value });

    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        setMessage('');
        setError('');
        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/profile`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(profile)
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Error al actualizar');
            setMessage('Perfil actualizado con éxito.');
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading && !profile.email) return <p>Cargando perfil...</p>;

    return (
        <div>
            <h2>Mi Perfil</h2>
            <form onSubmit={handleUpdateProfile}>
                <input name="full_name" value={profile.full_name || ''} onChange={handleInputChange} placeholder="Nombre Completo" />
                <input name="dui" value={profile.dui || ''} onChange={handleInputChange} placeholder="DUI" />
                <input name="nit" value={profile.nit || ''} onChange={handleInputChange} placeholder="NIT" />
                <button type="submit" disabled={isLoading}>{isLoading ? 'Guardando...' : 'Guardar Cambios'}</button>
                {error && <p style={{ color: 'red' }}>{error}</p>}
                {message && <p style={{ color: 'green' }}>{message}</p>}
            </form>
        </div>
    );
}