// frontend/MakeIntegrationView.js

function MakeIntegrationView() {
    const [scenarios, setScenarios] = React.useState([]);
    const [showForm, setShowForm] = React.useState(false);
    const [isLoading, setIsLoading] = React.useState(false);
    const [error, setError] = React.useState('');

    const API_URL = 'http://127.0.0.1:5001/api/make';
    const getAuthToken = () => localStorage.getItem('accessToken');

    const fetchScenarios = () => {
        setIsLoading(true);
        fetch(`${API_URL}/scenarios`, {
            headers: { 'Authorization': `Bearer ${getAuthToken()}` }
        })
        .then(res => res.json())
        .then(data => {
            setScenarios(data);
            setIsLoading(false);
        })
        .catch(err => {
            setError('Error al cargar los escenarios.');
            console.error(err);
            setIsLoading(false);
        });
    };

    React.useEffect(() => {
        fetchScenarios();
    }, []);

    const handleSaveScenario = (event) => {
        event.preventDefault();
        const { name, scenario_blueprint } = event.target.elements;

        let parsedJson;
        try {
            parsedJson = JSON.parse(scenario_blueprint.value);
        } catch (e) {
            setError("El JSON del blueprint no es válido.");
            return;
        }

        const data = {
            name: name.value,
            scenario_blueprint: parsedJson
        };

        setIsLoading(true);
        fetch(`${API_URL}/scenarios`, {
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
            fetchScenarios(); // Refresh list
        })
        .catch(err => {
            setError('Error al guardar el escenario.');
            console.error(err);
            setIsLoading(false);
        });
    };

    return (
        <div style={{ fontFamily: 'Arial, sans-serif', padding: '20px' }}>
            <h1 style={{ color: '#1a365d' }}>Integración con Make.com (LAN-MKE1)</h1>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <button onClick={() => setShowForm(!showForm)} style={{ marginBottom: '20px' }}>
                {showForm ? 'Cancelar' : 'Añadir Nuevo Escenario'}
            </button>

            {showForm && (
                <form onSubmit={handleSaveScenario} style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '5px', marginBottom: '20px' }}>
                    <h2>Nuevo Escenario</h2>
                    <div style={{ marginBottom: '10px' }}>
                        <label>Nombre:</label><br/>
                        <input type="text" name="name" required style={{ width: '100%', padding: '8px' }}/>
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                        <label>Blueprint del Escenario (JSON):</label><br/>
                        <textarea name="scenario_blueprint" required style={{ width: '100%', minHeight: '150px', padding: '8px' }}></textarea>
                    </div>
                    <button type="submit" disabled={isLoading}>{isLoading ? 'Guardando...' : 'Guardar Escenario'}</button>
                </form>
            )}

            <h2>Escenarios Existentes</h2>
            {isLoading && scenarios.length === 0 ? <p>Cargando...</p> : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ backgroundColor: '#f2f2f2' }}>
                            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Nombre</th>
                            <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {scenarios.map(s => (
                            <tr key={s.id}>
                                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{s.name}</td>
                                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{s.is_active ? 'Activo' : 'Inactivo'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}
