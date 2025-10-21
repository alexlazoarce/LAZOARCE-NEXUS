// frontend/SignerView.js

const SignerView = () => {
    const [templates, setTemplates] = React.useState([]);
    const [requests, setRequests] = React.useState([]);
    const [view, setView] = React.useState('requests'); // 'requests' or 'templates'

    const mockTemplates = [
        { id: 1, name: 'Propuesta de Servicios Estándar', description: 'Plantilla para nuevos clientes' },
        { id: 2, name: 'Acuerdo de Confidencialidad (NDA)', description: 'NDA estándar de la empresa' },
    ];

    const mockRequests = [
        { id: 1, signer_name: 'Juan Pérez', signer_email: 'juan.perez@example.com', status: 'signed', created_at: '2023-10-26T10:00:00Z' },
        { id: 2, signer_name: 'Ana Gómez', signer_email: 'ana.gomez@example.com', status: 'sent', created_at: '2023-10-25T15:30:00Z' },
        { id: 3, signer_name: 'Carlos Rivas', signer_email: 'carlos.rivas@example.com', status: 'viewed', created_at: '2023-10-24T11:00:00Z' },
    ];

    React.useEffect(() => {
        // Simulación de carga de datos
        setTemplates(mockTemplates);
        setRequests(mockRequests);
    }, []);

    const renderRequests = () => (
        <div className="card">
            <div className="card-header d-flex justify-content-between">
                <span>Solicitudes de Firma</span>
                <button className="btn btn-primary btn-sm">Nueva Solicitud</button>
            </div>
            <div className="card-body">
                <table className="table">
                    <thead>
                        <tr>
                            <th>Destinatario</th>
                            <th>Email</th>
                            <th>Estado</th>
                            <th>Fecha de Creación</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {requests.map(req => (
                            <tr key={req.id}>
                                <td>{req.signer_name}</td>
                                <td>{req.signer_email}</td>
                                <td><span className={`badge bg-${statusColor(req.status)}`}>{req.status}</span></td>
                                <td>{new Date(req.created_at).toLocaleString()}</td>
                                <td>
                                    <button className="btn btn-sm btn-info">Ver</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );

    const renderTemplates = () => (
        <div className="card">
            <div className="card-header d-flex justify-content-between">
                <span>Plantillas de Documentos</span>
                <button className="btn btn-primary btn-sm">Nueva Plantilla</button>
            </div>
            <div className="card-body">
                 <ul className="list-group">
                    {templates.map(t => (
                        <li key={t.id} className="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <h5>{t.name}</h5>
                                <p className="mb-0 text-muted">{t.description}</p>
                            </div>
                            <button className="btn btn-sm btn-secondary">Usar Plantilla</button>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );

    const statusColor = (status) => {
        switch(status) {
            case 'signed': return 'success';
            case 'sent': return 'info';
            case 'viewed': return 'warning';
            case 'declined': return 'danger';
            default: return 'secondary';
        }
    };

    return (
        <div className="container">
            <h2>LAN-SGN3: Firmar</h2>
            <ul className="nav nav-tabs mb-3">
                <li className="nav-item">
                    <a className={`nav-link ${view === 'requests' ? 'active' : ''}`} href="#" onClick={() => setView('requests')}>Solicitudes</a>
                </li>
                <li className="nav-item">
                    <a className={`nav-link ${view === 'templates' ? 'active' : ''}`} href="#" onClick={() => setView('templates')}>Plantillas</a>
                </li>
            </ul>

            {view === 'requests' ? renderRequests() : renderTemplates()}
        </div>
    );
};
