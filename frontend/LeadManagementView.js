const LeadManagementView = ({ token }) => {
    const [leads, setLeads] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    // Form for adding/editing a lead
    const [form, setForm] = React.useState({
        id: null, full_name: '', email: '', phone: '', status: 'Nuevo', source: '', notes: ''
    });
    const [isEditing, setIsEditing] = React.useState(false);

    // State for the detail view
    const [selectedLead, setSelectedLead] = React.useState(null);
    const [communications, setCommunications] = React.useState([]);
    const [newComm, setNewComm] = React.useState({ type: 'Llamada', notes: '' });

    const leadStatusOptions = ['Nuevo', 'Contactado', 'Calificado', 'No Calificado', 'Convertido a Cliente'];
    const commTypeOptions = ['Llamada', 'Email', 'Reunión'];

    const fetchLeads = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/leads`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudieron cargar los leads.');
            const data = await response.json();
            setLeads(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => { fetchLeads(); }, [token]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setForm(prev => ({ ...prev, [name]: value }));
    };

    const resetForm = () => {
        setForm({ id: null, full_name: '', email: '', phone: '', status: 'Nuevo', source: '', notes: '' });
        setIsEditing(false);
    };

    const handleEditClick = (lead) => {
        setForm(lead);
        setIsEditing(true);
        setSelectedLead(null); // Close detail view when editing
    };

    const handleSelectLead = async (lead) => {
        setSelectedLead(lead);
        setIsEditing(false); // Close edit form
        try {
            const response = await fetch(`${API_BASE_URL}/api/leads/${lead.id}/communications`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudieron cargar las comunicaciones.');
            const data = await response.json();
            setCommunications(data);
        } catch (err) {
            setError(err.message);
        }
    };

    const handleAddCommunication = async (e) => {
        e.preventDefault();
        if (!selectedLead) return;
        try {
            await fetch(`${API_BASE_URL}/api/leads/${selectedLead.id}/communications`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(newComm)
            });
            setNewComm({ type: 'Llamada', notes: '' });
            handleSelectLead(selectedLead); // Refresh
        } catch (err) { setError(err.message); }
    };

    const handleConvert = async (leadId) => {
        if (!window.confirm('¿Convertir este lead en cliente?')) return;
        try {
            const response = await fetch(`${API_BASE_URL}/api/leads/${leadId}/convert`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message);
            alert(data.message);
            fetchLeads();
        } catch (err) { alert(`Error: ${err.message}`); }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const url = isEditing ? `${API_BASE_URL}/api/leads/${form.id}` : `${API_BASE_URL}/api/leads`;
        const method = isEditing ? 'PUT' : 'POST';
        try {
            await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(form)
            });
            resetForm();
            fetchLeads();
        } catch (err) { setError(err.message); }
    };

    if (loading) return <p>Cargando...</p>;

    return (
        <div>
            <h3>Gestión de Clientes Potenciales (Leads)</h3>
            {error && <p className="error" style={{color: 'red'}}>{error}</p>}
            <div style={{ display: 'flex', gap: '20px' }}>
                <div style={{ flex: 2 }}>
                    <form onSubmit={handleSubmit} style={{ marginBottom: '20px', border: '1px solid #ccc', padding: '10px' }}>
                        <h4>{isEditing ? 'Editar Lead' : 'Agregar Nuevo Lead'}</h4>
                        <input name="full_name" value={form.full_name} onChange={handleInputChange} placeholder="Nombre Completo" required />
                        <input type="email" name="email" value={form.email} onChange={handleInputChange} placeholder="Email" />
                        <input name="phone" value={form.phone} onChange={handleInputChange} placeholder="Teléfono" />
                        <input name="source" value={form.source} onChange={handleInputChange} placeholder="Fuente (ej. Web)" />
                        <select name="status" value={form.status} onChange={handleInputChange}>
                            {leadStatusOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                        </select>
                        <textarea name="notes" value={form.notes} onChange={handleInputChange} placeholder="Notas..."></textarea>
                        <button type="submit">{isEditing ? 'Actualizar' : 'Agregar'}</button>
                        {isEditing && <button type="button" onClick={resetForm}>Cancelar</button>}
                    </form>
                    <table>
                        <thead><tr><th>Nombre</th><th>Email</th><th>Estado</th><th>Acciones</th></tr></thead>
                        <tbody>
                            {leads.map(lead => (
                                <tr key={lead.id}>
                                    <td><button className="link-button" onClick={() => handleSelectLead(lead)}>{lead.full_name}</button></td>
                                    <td>{lead.email}</td>
                                    <td>{lead.status}</td>
                                    <td>
                                        <button onClick={() => handleEditClick(lead)}>Editar</button>
                                        {lead.status === 'Calificado' && (
                                            <button onClick={() => handleConvert(lead.id)} style={{marginLeft: '5px'}}>Convertir</button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div style={{ flex: 1, borderLeft: '2px solid #eee', paddingLeft: '20px' }}>
                    {selectedLead ? (
                        <div>
                            <h4>Detalle de: {selectedLead.full_name}</h4>
                            <p><strong>Teléfono:</strong> {selectedLead.phone}</p>
                            <p><strong>Fuente:</strong> {selectedLead.source}</p>
                            <p><strong>Notas Generales:</strong> {selectedLead.notes}</p>
                            <hr/>
                            <h5>Historial de Comunicación</h5>
                            {communications.map(comm => (
                                <div key={comm.id} style={{border: '1px solid #ddd', padding: '5px', marginBottom: '5px'}}>
                                    <p><strong>{comm.type}</strong> por {comm.employee_name} el {new Date(comm.timestamp).toLocaleString()}</p>
                                    <p>{comm.notes}</p>
                                </div>
                            ))}
                            <hr/>
                            <h5>Agregar Comunicación</h5>
                            <form onSubmit={handleAddCommunication}>
                                <select value={newComm.type} onChange={e => setNewComm({...newComm, type: e.target.value})}>
                                    {commTypeOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                                </select>
                                <textarea value={newComm.notes} onChange={e => setNewComm({...newComm, notes: e.target.value})} placeholder="Detalles..." required></textarea>
                                <button type="submit">Registrar</button>
                            </form>
                        </div>
                    ) : <p>Seleccione un lead para ver detalles.</p>}
                </div>
            </div>
        </div>
    );
};