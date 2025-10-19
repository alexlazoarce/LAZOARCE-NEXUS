// frontend/AutomationView.js

function AutomationView() {
    const [workflows, setWorkflows] = React.useState([]);
    const [showForm, setShowForm] = React.useState(false);
    const [isLoading, setIsLoading] = React.useState(false);
    const [error, setError] = React.useState('');

    const API_URL = 'http://127.0.0.1:5001/api/automations';
    const getAuthToken = () => localStorage.getItem('accessToken');

    const fetchWorkflows = () => {
        setIsLoading(true);
        fetch(`${API_URL}/workflows`, {
            headers: { 'Authorization': `Bearer ${getAuthToken()}` }
        })
        .then(res => res.json())
        .then(data => {
            setWorkflows(data);
            setIsLoading(false);
        })
        .catch(err => {
            setError('Error al cargar los flujos de trabajo.');
            console.error(err);
            setIsLoading(false);
        });
    };

    React.useEffect(() => {
        fetchWorkflows();
    }, []);

    const handleSaveWorkflow = (event) => {
        event.preventDefault();
        const { name, trigger_event, workflow_json } = event.target.elements;

        let parsedJson;
        try {
            parsedJson = JSON.parse(workflow_json.value);
        } catch (e) {
            setError("El JSON del flujo de trabajo no es válido.");
            return;
        }

        const data = {
            name: name.value,
            trigger_event: trigger_event.value,
            workflow_json: parsedJson
        };

        setIsLoading(true);
        fetch(`${API_URL}/workflows`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(() => {
            setShowForm(false);
            fetchWorkflows(); // Refresh list
        })
        .catch(err => {
            setError('Error al guardar el flujo de trabajo.');
            console.error(err);
            setIsLoading(false);
        });
    };

    return (
        <div style={{ fontFamily: 'Arial, sans-serif', padding: '20px' }}>
            <h1 style={{ color: '#1a365d' }}>Gestión de Automatización (LAN-N8N1)</h1>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <button onClick={() => setShowForm(!showForm)} style={{ marginBottom: '20px' }}>
                {showForm ? 'Cancelar' : 'Añadir Nuevo Flujo de Trabajo'}
            </button>

            {showForm && (
                <form onSubmit={handleSaveWorkflow} style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '5px', marginBottom: '20px' }}>
                    <h2>Nuevo Flujo de Trabajo</h2>
                    <div style={{ marginBottom: '10px' }}>
                        <label>Nombre:</label><br/>
                        <input type="text" name="name" required style={{ width: '100%', padding: '8px' }}/>
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                        <label>Evento de Disparo (Trigger):</label><br/>
                        <input type="text" name="trigger_event" placeholder="ej: whatsapp_message_received" required style={{ width: '100%', padding: '8px' }}/>
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                        <label>Definición del Flujo (JSON):</label><br/>
                        <textarea name="workflow_json" required style={{ width: '100%', minHeight: '150px', padding: '8px' }}></textarea>
                    </div>
                    <button type="submit" disabled={isLoading}>{isLoading ? 'Guardando...' : 'Guardar Flujo'}</button>
                </form>
            )}

            <h2>Flujos de Trabajo Existentes</h2>
            {isLoading && workflows.length === 0 ? <p>Cargando...</p> : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ backgroundColor: '#f2f2f2' }}>
                            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Nombre</th>
                            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Trigger</th>
                            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {workflows.map(w => (
                            <tr key={w.id}>
                                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{w.name}</td>
                                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{w.trigger_event}</td>
                                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{w.is_active ? 'Activo' : 'Inactivo'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}
