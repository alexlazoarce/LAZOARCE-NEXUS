const API_BASE_URL = 'http://127.0.0.1:5000';

function Profile({ token }) {
    const [profileData, setProfileData] = React.useState({
        email: '',
        full_name: '',
        dui: '',
        nit: ''
    });
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [success, setSuccess] = React.useState('');

    React.useEffect(() => {
        const fetchProfile = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/profile`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.msg);
                setProfileData(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, [token]);

    const handleChange = (e) => {
        setProfileData({ ...profileData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        try {
            const res = await fetch(`${API_BASE_URL}/api/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    full_name: profileData.full_name,
                    dui: profileData.dui,
                    nit: profileData.nit
                })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg);
            setSuccess(data.msg);
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) {
        return <p>Cargando perfil...</p>;
    }

    return (
        <div className="profile-container">
            <h3>Mi Perfil</h3>
            <p>Esta información se utilizará para generar los contratos de préstamo.</p>
            <form onSubmit={handleSubmit} className="form-section" style={{maxWidth: '500px'}}>
                <div className="form-group">
                    <label>Email</label>
                    <input type="email" value={profileData.email} disabled />
                </div>
                <div className="form-group">
                    <label>Nombre Completo</label>
                    <input type="text" name="full_name" value={profileData.full_name || ''} onChange={handleChange} />
                </div>
                <div className="form-group">
                    <label>DUI (Documento Único de Identidad)</label>
                    <input type="text" name="dui" value={profileData.dui || ''} onChange={handleChange} />
                </div>
                <div className="form-group">
                    <label>NIT (Número de Identificación Tributaria)</label>
                    <input type="text" name="nit" value={profileData.nit || ''} onChange={handleChange} />
                </div>

                {error && <p style={{color: 'red'}}>Error: {error}</p>}
                {success && <p style={{color: 'green'}}>{success}</p>}

                <button type="submit">Guardar Cambios</button>
            </form>
        </div>
    );
}