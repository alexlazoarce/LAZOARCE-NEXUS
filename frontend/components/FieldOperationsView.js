const FieldOperationsView = () => {
    const [tasks, setTasks] = React.useState([]);
    const [showTaskModal, setShowTaskModal] = React.useState(false);

    const api = useApi();

    const fetchTasks = async () => {
        try {
            const response = await api.get('/api/field-ops/tasks');
            setTasks(response.data || []);
        } catch (error) {
            console.error("Error fetching field tasks:", error);
            alert('Error al cargar las tareas de campo.');
        }
    };

    React.useEffect(() => {
        fetchTasks();
    }, []);

    const handleCreateTask = async (event) => {
        event.preventDefault();
        const data = Object.fromEntries(new FormData(event.target).entries());
        try {
            await api.post('/api/field-ops/tasks', data);
            setShowTaskModal(false);
            fetchTasks();
            alert('Tarea de campo creada con éxito.');
        } catch (error) {
            console.error("Error creating field task:", error);
            alert('Error al crear la tarea de campo.');
        }
    };

    return (
        <div className="container-fluid">
            <h1>Operaciones de Campo (LAN-FLD2)</h1>
            <p>Rutas GPS para técnicos, seguimiento de tareas en sitio, gestión de materiales y reportes de avance con geolocalización.</p>

            <div className="card">
                <div className="card-header d-flex justify-content-between align-items-center">
                    Tareas Asignadas
                    <button className="btn btn-sm btn-primary" onClick={() => setShowTaskModal(true)}>Nueva Tarea</button>
                </div>
                <div className="card-body">
                    <table className="table table-striped">
                        <thead>
                            <tr>
                                <th>Título</th>
                                <th>Asignado a</th>
                                <th>Dirección</th>
                                <th>Fecha Límite</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tasks.map(task => (
                                <tr key={task.id}>
                                    <td>{task.title}</td>
                                    <td>{task.assigned_to_id}</td>
                                    <td>{task.address}</td>
                                    <td>{task.due_date}</td>
                                    <td><span className="badge bg-info">{task.status}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {showTaskModal && (
                 <div className="modal show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}><div className="modal-dialog">
                    <div className="modal-content">
                        <form onSubmit={handleCreateTask}>
                            <div className="modal-header"><h5 className="modal-title">Nueva Tarea de Campo</h5><button type="button" className="btn-close" onClick={() => setShowTaskModal(false)}></button></div>
                            <div className="modal-body">
                                <div className="mb-3"><label className="form-label">Título</label><input type="text" className="form-control" name="title" required /></div>
                                <div className="mb-3"><label className="form-label">Asignado a (ID de Usuario)</label><input type="number" className="form-control" name="assigned_to_id" required /></div>
                                <div className="mb-3"><label className="form-label">Dirección</label><textarea className="form-control" name="address"></textarea></div>
                                <div className="mb-3"><label className="form-label">Fecha Límite</label><input type="date" className="form-control" name="due_date" /></div>
                            </div>
                            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowTaskModal(false)}>Cerrar</button><button type="submit" className="btn btn-primary">Crear Tarea</button></div>
                        </form>
                    </div>
                </div></div>
            )}
        </div>
    );
};
