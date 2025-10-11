const TemplateManagerView = ({ token }) => {
    const [templates, setTemplates] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    const [selectedTemplate, setSelectedTemplate] = React.useState(null);
    const [form, setForm] = React.useState({ id: null, subject: '', body: '' });

    const fetchTemplates = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/templates`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudieron cargar las plantillas.');
            const data = await response.json();
            setTemplates(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchTemplates();
    }, [token]);

    const handleSelectTemplate = (template) => {
        setSelectedTemplate(template);
        setForm(template);
    };

    const handleFormChange = (e) => {
        const { name, value } = e.target;
        setForm(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedTemplate) return;
        try {
            const response = await fetch(`${API_BASE_URL}/api/templates/${selectedTemplate.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ subject: form.subject, body: form.body })
            });
            if (!response.ok) throw new Error('Error al actualizar la plantilla.');
            alert('Plantilla actualizada con éxito!');
            fetchTemplates(); // Refresh the list
            setSelectedTemplate(null); // Close the form
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) return <p>Cargando plantillas...</p>;
    if (error) return <p className="error" style={{color: 'red'}}>{error}</p>;

    return (
        <div>
            <h3>Gestor de Plantillas de Notificación</h3>
            <div style={{ display: 'flex', gap: '20px' }}>
                <div style={{ flex: 1 }}>
                    <h4>Plantillas Disponibles</h4>
                    <ul>
                        {templates.map(t => (
                            <li key={t.id}>
                                <button className="link-button" onClick={() => handleSelectTemplate(t)}>
                                    {t.slug}
                                </button>
                                ({t.subject})
                            </li>
                        ))}
                    </ul>
                </div>
                <div style={{ flex: 2, borderLeft: '1px solid #ccc', paddingLeft: '20px' }}>
                    {selectedTemplate ? (
                        <form onSubmit={handleSubmit}>
                            <h4>Editando: {selectedTemplate.slug}</h4>
                            <p>Puedes usar variables como {'{customer_name}'}, {'{amount}'}, etc.</p>
                            <div>
                                <label>Asunto:</label>
                                <input
                                    type="text"
                                    name="subject"
                                    value={form.subject}
                                    onChange={handleFormChange}
                                    style={{width: '100%'}}
                                />
                            </div>
                            <div style={{marginTop: '10px'}}>
                                <label>Cuerpo del Mensaje:</label>
                                <textarea
                                    name="body"
                                    value={form.body}
                                    onChange={handleFormChange}
                                    rows="10"
                                    style={{width: '100%'}}
                                ></textarea>
                            </div>
                            <button type="submit">Guardar Cambios</button>
                            <button type="button" onClick={() => setSelectedTemplate(null)}>Cancelar</button>
                        </form>
                    ) : (
                        <p>Selecciona una plantilla para editarla.</p>
                    )}
                </div>
            </div>
        </div>
    );
};