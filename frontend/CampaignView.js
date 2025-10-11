const CampaignView = ({ token }) => {
    const [campaigns, setCampaigns] = React.useState([]);
    const [mailingLists, setMailingLists] = React.useState([]);
    const [templates, setTemplates] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    // Form state for new campaign
    const [form, setForm] = React.useState({ name: '', subject: '', mailing_list_id: '', template_id: '' });

    const fetchData = async () => {
        try {
            setLoading(true);
            const [c, l, t] = await Promise.all([
                fetch(`${API_BASE_URL}/api/campaigns`, { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/api/mailing-lists`, { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/api/templates`, { headers: { 'Authorization': `Bearer ${token}` } })
            ]);
            if (!c.ok || !l.ok || !t.ok) throw new Error('Error al cargar datos de marketing.');

            setCampaigns(await c.json());
            setMailingLists(await l.json());
            setTemplates(await t.json());
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => { fetchData(); }, [token]);

    const handleFormChange = (e) => {
        const { name, value } = e.target;
        setForm(prev => ({ ...prev, [name]: value }));
    };

    const handleCreateCampaign = async (e) => {
        e.preventDefault();
        try {
            await fetch(`${API_BASE_URL}/api/campaigns`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(form)
            });
            setForm({ name: '', subject: '', mailing_list_id: '', template_id: '' });
            fetchData();
        } catch (err) { setError(err.message); }
    };

    const handleSendCampaign = async (campaignId) => {
        if (!window.confirm('¿Está seguro de que desea enviar esta campaña? Esta acción no se puede deshacer.')) return;
        try {
            const response = await fetch(`${API_BASE_URL}/api/campaigns/${campaignId}/send`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message);
            alert(data.message);
            fetchData();
        } catch (err) { alert(`Error: ${err.message}`); }
    };

    if (loading) return <p>Cargando...</p>;

    return (
        <div>
            <h3>Gestión de Campañas de Email</h3>
            {error && <p style={{color: 'red'}}>{error}</p>}

            <form onSubmit={handleCreateCampaign} style={{border: '1px solid #ccc', padding: '10px', marginBottom: '20px'}}>
                <h4>Crear Nueva Campaña</h4>
                <input name="name" value={form.name} onChange={handleFormChange} placeholder="Nombre de la Campaña" required />
                <input name="subject" value={form.subject} onChange={handleFormChange} placeholder="Asunto del Email" required />
                <select name="mailing_list_id" value={form.mailing_list_id} onChange={handleFormChange} required>
                    <option value="">-- Seleccione una Lista --</option>
                    {mailingLists.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                </select>
                <select name="template_id" value={form.template_id} onChange={handleFormChange} required>
                    <option value="">-- Seleccione una Plantilla --</option>
                    {templates.map(t => <option key={t.id} value={t.id}>{t.slug}</option>)}
                </select>
                <button type="submit">Crear Campaña</button>
            </form>

            <table>
                <thead><tr><th>Nombre</th><th>Asunto</th><th>Lista</th><th>Plantilla</th><th>Estado</th><th>Acciones</th></tr></thead>
                <tbody>
                    {campaigns.map(c => (
                        <tr key={c.id}>
                            <td>{c.name}</td>
                            <td>{c.subject}</td>
                            <td>{c.mailing_list_name}</td>
                            <td>{c.template_slug}</td>
                            <td>{c.status}</td>
                            <td>{c.status === 'Draft' && <button onClick={() => handleSendCampaign(c.id)}>Enviar</button>}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};