function CADView() {
    const [projects, setProjects] = React.useState([]);
    const [newProjectName, setNewProjectName] = React.useState('');
    const [selectedProject, setSelectedProject] = React.useState(null);

    React.useEffect(() => {
        // Cargar proyectos iniciales
        fetchProjects();
    }, []);

    const fetchProjects = () => {
        // Simulación de fetch
        console.log("Fetching CAD projects...");
        // En una aplicación real, aquí llamarías a tu API:
        // api.get('/cad/projects').then(response => setProjects(response.data));
        setProjects([
            { id: 1, name: 'Proyecto Residencial A', description: 'Planos para casa de playa.' },
            { id: 2, name: 'Edificio Comercial B', description: 'Diseño estructural del centro comercial.' }
        ]);
    };

    const handleCreateProject = () => {
        if (!newProjectName.trim()) {
            alert('El nombre del proyecto no puede estar vacío.');
            return;
        }
        console.log(`Creating project: ${newProjectName}`);
        // Simulación de creación
        const newProject = {
            id: projects.length + 1,
            name: newProjectName,
            description: 'Nuevo proyecto creado desde la UI.'
        };
        setProjects([...projects, newProject]);
        setNewProjectName('');
    };

    return (
        <div className="container">
            <h1>Gestión de Planos (LAN-CAD)</h1>
            <div className="card">
                <div className="card-header">
                    Crear Nuevo Proyecto
                </div>
                <div className="card-body">
                    <div className="input-group mb-3">
                        <input
                            type="text"
                            className="form-control"
                            placeholder="Nombre del Nuevo Proyecto"
                            value={newProjectName}
                            onChange={(e) => setNewProjectName(e.target.value)}
                        />
                        <div className="input-group-append">
                            <button className="btn btn-primary" type="button" onClick={handleCreateProject}>
                                Crear Proyecto
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="card mt-4">
                <div className="card-header">
                    Lista de Proyectos
                </div>
                <ul className="list-group list-group-flush">
                    {projects.length > 0 ? projects.map(p => (
                        <li key={p.id} className="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <h5>{p.name}</h5>
                                <p className="mb-0">{p.description}</p>
                            </div>
                            <button className="btn btn-sm btn-info" onClick={() => setSelectedProject(p)}>
                                Ver Detalles
                            </button>
                        </li>
                    )) : (
                        <li className="list-group-item">No hay proyectos para mostrar.</li>
                    )}
                </ul>
            </div>

            {selectedProject && (
                <div className="modal" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">Detalles del Proyecto: {selectedProject.name}</h5>
                                <button type="button" className="close" onClick={() => setSelectedProject(null)}>
                                    <span>&times;</span>
                                </button>
                            </div>
                            <div className="modal-body">
                                <p><strong>ID:</strong> {selectedProject.id}</p>
                                <p><strong>Nombre:</strong> {selectedProject.name}</p>
                                <p><strong>Descripción:</strong> {selectedProject.description}</p>
                                <p><em>(Aquí se mostrarían los archivos, capas y sesiones de colaboración.)</em></p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
