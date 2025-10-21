// frontend/SupportTicketView.js

const SupportTicketView = () => {
    const [tickets, setTickets] = React.useState([]);
    const [selectedTicket, setSelectedTicket] = React.useState(null);
    // Asumimos un rol para el mock; en la app real vendría del contexto de usuario
    const userRole = 'Cliente'; // Cambiar a 'Soporte' para ver la otra vista

    const mockTickets = [
        { id: 1, subject: 'Problema con la facturación', status: 'Abierto', priority: 'Alta', updated_at: '2023-10-26T10:00:00Z' },
        { id: 2, subject: 'Consulta sobre el módulo de Proyectos', status: 'En Progreso', priority: 'Media', updated_at: '2023-10-25T15:30:00Z' },
        { id: 3, subject: 'No puedo iniciar sesión', status: 'Cerrado', priority: 'Alta', updated_at: '2023-10-24T11:00:00Z' },
    ];

    const mockUpdates = {
        1: [{ id: 101, author: 'Juan Pérez', comment: 'Mi factura de este mes parece incorrecta.', created_at: '2023-10-26T10:00:00Z' }],
        2: [
            { id: 201, author: 'Ana Gómez', comment: '¿Cómo puedo asignar una tarea a otro usuario?', created_at: '2023-10-25T15:30:00Z' },
            { id: 202, author: 'Equipo de Soporte', comment: 'Hola Ana, puedes hacerlo desde la vista de detalle del proyecto...', created_at: '2023-10-25T16:00:00Z' }
        ],
        3: []
    };

    React.useEffect(() => {
        setTickets(mockTickets);
    }, []);

    const statusColor = (status) => {
        if (status === 'Abierto') return 'danger';
        if (status === 'En Progreso') return 'warning';
        return 'success';
    };

    if (selectedTicket) {
        return (
            <div className="container">
                <button className="btn btn-secondary mb-3" onClick={() => setSelectedTicket(null)}>
                    &larr; Volver a los Tickets
                </button>
                <h3>{selectedTicket.subject}</h3>
                <p>
                    <span className={`badge bg-${statusColor(selectedTicket.status)}`}>{selectedTicket.status}</span>
                </p>
                <div className="card">
                    <div className="card-header">Historial del Ticket</div>
                    <div className="card-body">
                        {(mockUpdates[selectedTicket.id] || []).map(update => (
                            <div key={update.id} className="mb-3">
                                <strong>{update.author}</strong> <small className="text-muted">{new Date(update.created_at).toLocaleString()}</small>
                                <p>{update.comment}</p>
                            </div>
                        ))}
                    </div>
                    <div className="card-footer">
                        <textarea className="form-control mb-2" placeholder="Escribe una respuesta..."></textarea>
                        <button className="btn btn-primary">Añadir Actualización</button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="container">
            <h2>LAN-SOP1: Soporte Técnico</h2>
            <div className="card">
                <div className="card-header d-flex justify-content-between">
                    <span>{userRole === 'Cliente' ? 'Mis Tickets de Soporte' : 'Panel de Soporte'}</span>
                    {userRole === 'Cliente' && <button className="btn btn-primary btn-sm">Crear Nuevo Ticket</button>}
                </div>
                <div className="card-body">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Asunto</th>
                                <th>Estado</th>
                                <th>Prioridad</th>
                                <th>Última Actualización</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tickets.map(ticket => (
                                <tr key={ticket.id}>
                                    <td>{ticket.subject}</td>
                                    <td><span className={`badge bg-${statusColor(ticket.status)}`}>{ticket.status}</span></td>
                                    <td>{ticket.priority}</td>
                                    <td>{new Date(ticket.updated_at).toLocaleString()}</td>
                                    <td>
                                        <button className="btn btn-sm btn-info" onClick={() => setSelectedTicket(ticket)}>
                                            Ver Detalles
                                        </button>
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
