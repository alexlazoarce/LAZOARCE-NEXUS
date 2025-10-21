// frontend/FormBuilderView.js

const FormBuilderView = () => {
    const [forms, setForms] = React.useState([]);
    const [viewingSubmissions, setViewingSubmissions] = React.useState(null); // form object
    const [submissions, setSubmissions] = React.useState([]);

    const mockForms = [
        { id: 1, name: 'Formulario de Contacto', public_token: 'abc-123', fieldCount: 3 },
        { id: 2, name: 'Encuesta de Satisfacción', public_token: 'def-456', fieldCount: 5 },
    ];

    const mockSubmissions = {
        1: [
            { id: 101, data: { nombre: 'Juan', email: 'juan@test.com' }, submitted_at: '2023-10-26T10:00:00Z' },
            { id: 102, data: { nombre: 'Ana', email: 'ana@test.com' }, submitted_at: '2023-10-26T11:30:00Z' },
        ],
        2: [
            { id: 201, data: { calificacion: 5, comentarios: 'Excelente servicio' }, submitted_at: '2023-10-25T14:00:00Z' },
        ]
    };

    React.useEffect(() => {
        setForms(mockForms);
    }, []);

    const handleViewSubmissions = (form) => {
        setViewingSubmissions(form);
        setSubmissions(mockSubmissions[form.id] || []);
    };

    if (viewingSubmissions) {
        return (
            <div className="container">
                <button className="btn btn-secondary mb-3" onClick={() => setViewingSubmissions(null)}>
                    &larr; Volver a Formularios
                </button>
                <h2>Envíos para: {viewingSubmissions.name}</h2>
                <div className="card">
                    <div className="card-body">
                        {submissions.length === 0 ? <p>No hay envíos para este formulario.</p> : (
                            <ul className="list-group">
                                {submissions.map(sub => (
                                    <li key={sub.id} className="list-group-item">
                                        <p><strong>Fecha:</strong> {new Date(sub.submitted_at).toLocaleString()}</p>
                                        <pre>{JSON.stringify(sub.data, null, 2)}</pre>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="container">
            <h2>LAN-FRM5: Gestor de Formularios</h2>
            <div className="card">
                <div className="card-header d-flex justify-content-between">
                    <span>Mis Formularios</span>
                    <button className="btn btn-primary btn-sm">Crear Nuevo Formulario</button>
                </div>
                <div className="card-body">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Nombre del Formulario</th>
                                <th>Token Público</th>
                                <th>Campos</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {forms.map(form => (
                                <tr key={form.id}>
                                    <td>{form.name}</td>
                                    <td><code>{form.public_token}</code></td>
                                    <td>{form.fieldCount}</td>
                                    <td>
                                        <button className="btn btn-sm btn-info me-2" onClick={() => handleViewSubmissions(form)}>
                                            Ver Envíos
                                        </button>
                                        <button className="btn btn-sm btn-secondary">Editar</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
