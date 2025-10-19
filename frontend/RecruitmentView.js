// frontend/RecruitmentView.js

function RecruitmentView() {
    const [vacancies, setVacancies] = React.useState([]);
    const [selectedVacancy, setSelectedVacancy] = React.useState(null);
    const [applications, setApplications] = React.useState([]);
    const [showVacancyForm, setShowVacancyForm] = React.useState(false);
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);

    const API_URL = 'http://127.0.0.1:5001/api';

    const getAuthToken = () => {
        return localStorage.getItem('accessToken');
    };

    const fetchVacancies = () => {
        setIsLoading(true);
        fetch(`${API_URL}/recruitment/vacancies`, {
            headers: { 'Authorization': `Bearer ${getAuthToken()}` }
        })
        .then(response => response.json())
        .then(data => {
            setVacancies(data);
            setIsLoading(false);
        })
        .catch(err => {
            setError('Error al cargar las vacantes.');
            setIsLoading(false);
            console.error(err);
        });
    };

    const fetchApplications = (vacancyId) => {
        setIsLoading(true);
        fetch(`${API_URL}/recruitment/vacancies/${vacancyId}/applications`, {
            headers: { 'Authorization': `Bearer ${getAuthToken()}` }
        })
        .then(response => response.json())
        .then(data => {
            setApplications(data);
            setIsLoading(false);
        })
        .catch(err => {
            setError(`Error al cargar las aplicaciones para la vacante ${vacancyId}.`);
            setIsLoading(false);
            console.error(err);
        });
    };

    React.useEffect(() => {
        fetchVacancies();
    }, []);

    const handleVacancySelect = (vacancy) => {
        setSelectedVacancy(vacancy);
        fetchApplications(vacancy.id);
    };

    const handleCreateVacancy = (event) => {
        event.preventDefault();
        const { title, description } = event.target.elements;

        const vacancyData = {
            title: title.value,
            description: description.value,
        };

        fetch(`${API_URL}/recruitment/vacancies`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify(vacancyData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al crear la vacante.');
            }
            return response.json();
        })
        .then(() => {
            setShowVacancyForm(false);
            fetchVacancies(); // Refresh the list
        })
        .catch(err => {
            setError(err.message);
            console.error(err);
        });
    };

    const handleUpdateStatus = (applicationId, newStatus) => {
        fetch(`${API_URL}/recruitment/applications/${applicationId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => response.json())
        .then(() => {
            // Refresh applications for the selected vacancy
            fetchApplications(selectedVacancy.id);
        })
        .catch(err => {
            setError('Error al actualizar el estado de la aplicación.');
            console.error(err);
        });
    };

    return (
        <div style={{ fontFamily: 'Arial, sans-serif', padding: '20px', color: '#333' }}>
            <h1 style={{ color: '#1a365d' }}>Módulo de Reclutamiento (LAN-REC7)</h1>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <button
                onClick={() => setShowVacancyForm(!showVacancyForm)}
                style={{ backgroundColor: '#1a365d', color: 'white', padding: '10px 15px', border: 'none', borderRadius: '5px', cursor: 'pointer', marginBottom: '20px' }}>
                {showVacancyForm ? 'Cancelar' : 'Crear Nueva Vacante'}
            </button>

            {showVacancyForm && (
                <form onSubmit={handleCreateVacancy} style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ccc', borderRadius: '5px' }}>
                    <h2 style={{ color: '#1a365d' }}>Nueva Vacante</h2>
                    <div style={{ marginBottom: '10px' }}>
                        <label>Título:</label><br/>
                        <input type="text" name="title" required style={{ width: '100%', padding: '8px' }}/>
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                        <label>Descripción:</label><br/>
                        <textarea name="description" required style={{ width: '100%', padding: '8px', minHeight: '100px' }}></textarea>
                    </div>
                    <button type="submit" style={{ backgroundColor: '#059669', color: 'white', padding: '10px 15px', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
                        Guardar Vacante
                    </button>
                </form>
            )}

            <div style={{ display: 'flex', gap: '20px' }}>
                <div style={{ flex: 1 }}>
                    <h2 style={{ color: '#1a365d' }}>Vacantes Abiertas</h2>
                    {isLoading && <p>Cargando...</p>}
                    <ul style={{ listStyleType: 'none', padding: 0 }}>
                        {vacancies.map(v => (
                            <li key={v.id}
                                onClick={() => handleVacancySelect(v)}
                                style={{ padding: '10px', border: '1px solid #ccc', marginBottom: '5px', borderRadius: '5px', cursor: 'pointer', backgroundColor: selectedVacancy && selectedVacancy.id === v.id ? '#e0e7ff' : 'white' }}>
                                <strong>{v.title}</strong> ({v.status})
                            </li>
                        ))}
                    </ul>
                </div>
                <div style={{ flex: 2 }}>
                    <h2 style={{ color: '#1a365d' }}>Aplicaciones</h2>
                    {selectedVacancy ? (
                        <div>
                            <h3>Aplicaciones para: {selectedVacancy.title}</h3>
                            {isLoading && <p>Cargando...</p>}
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ backgroundColor: '#f2f2f2' }}>
                                        <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Candidato</th>
                                        <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Email</th>
                                        <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Fecha</th>
                                        <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Estado</th>
                                        <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {applications.map(app => (
                                        <tr key={app.id}>
                                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>{app.candidate_name}</td>
                                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>{app.candidate_email}</td>
                                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>{new Date(app.application_date).toLocaleDateString()}</td>
                                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>{app.status}</td>
                                            <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                                                <select
                                                    value={app.status}
                                                    onChange={(e) => handleUpdateStatus(app.id, e.target.value)}
                                                    style={{ padding: '5px' }}>
                                                    <option value="Nuevo">Nuevo</option>
                                                    <option value="Revisión">Revisión</option>
                                                    <option value="Entrevista">Entrevista</option>
                                                    <option value="Oferta">Oferta</option>
                                                    <option value="Contratado">Contratado</option>
                                                    <option value="Rechazado">Rechazado</option>
                                                </select>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <p>Seleccione una vacante para ver las aplicaciones.</p>
                    )}
                </div>
            </div>
        </div>
    );
}
