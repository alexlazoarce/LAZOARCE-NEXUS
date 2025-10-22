// frontend/ProjectManagementView.js

const ProjectManagementView = () => {
    const [projects, setProjects] = React.useState([]);
    const [selectedProject, setSelectedProject] = React.useState(null);
    const [tasks, setTasks] = React.useState([]);

    const mockProjects = [
        { id: 1, name: 'Lanzamiento del Producto X', status: 'En Progreso', end_date: '2023-12-31' },
        { id: 2, name: 'Campaña de Marketing Q4', status: 'Planificado', end_date: '2023-11-30' },
        { id: 3, name: 'Actualización del Servidor', status: 'Completado', end_date: '2023-10-15' },
    ];

    const mockTasks = {
        1: [
            { id: 101, title: 'Diseñar wireframes', status: 'Completada', due_date: '2023-10-20' },
            { id: 102, title: 'Desarrollar API', status: 'En Progreso', due_date: '2023-11-05' },
            { id: 103, title: 'Realizar pruebas de usuario', status: 'Pendiente', due_date: '2023-11-15' },
        ],
        2: [
            { id: 201, title: 'Definir estrategia de redes sociales', status: 'Pendiente', due_date: '2023-10-28' },
        ],
        3: []
    };

    React.useEffect(() => {
        setProjects(mockProjects);
    }, []);

    const handleSelectProject = (project) => {
        setSelectedProject(project);
        setTasks(mockTasks[project.id] || []);
    };

    if (selectedProject) {
        return (
            <div className="container">
                <button className="btn btn-secondary mb-3" onClick={() => setSelectedProject(null)}>
                    &larr; Volver a Proyectos
                </button>
                <h2>{selectedProject.name} <span className={`badge bg-info`}>{selectedProject.status}</span></h2>

                <div className="card">
                    <div className="card-header d-flex justify-content-between">
                        <span>Tareas</span>
                        <button className="btn btn-primary btn-sm">Nueva Tarea</button>
                    </div>
                    <div className="card-body">
                        {tasks.length > 0 ? (
                            <ul className="list-group">
                                {tasks.map(task => (
                                    <li key={task.id} className="list-group-item">
                                        <h5>{task.title}</h5>
                                        <p className="mb-1">Estado: <span className={`badge bg-${task.status === 'Completada' ? 'success' : 'warning'}`}>{task.status}</span></p>
                                        <small>Vence: {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'N/A'}</small>
                                    </li>
                                ))}
                            </ul>
                        ) : <p>No hay tareas para este proyecto.</p>}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="container">
            <h2>LAN-PR0: Gestión de Proyectos</h2>
            <div className="card">
                <div className="card-header d-flex justify-content-between">
                    <span>Proyectos Activos</span>
                    <button className="btn btn-primary btn-sm">Crear Nuevo Proyecto</button>
                </div>
                <div className="card-body">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Nombre del Proyecto</th>
                                <th>Estado</th>
                                <th>Fecha de Finalización</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {projects.map(proj => (
                                <tr key={proj.id}>
                                    <td>{proj.name}</td>
                                    <td>{proj.status}</td>
                                    <td>{proj.end_date ? new Date(proj.end_date).toLocaleDateString() : 'N/A'}</td>
                                    <td>
                                        <button className="btn btn-sm btn-info" onClick={() => handleSelectProject(proj)}>
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
