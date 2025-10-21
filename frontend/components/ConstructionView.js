const ConstructionView = () => {
    const [projects, setProjects] = React.useState([]);
    const [selectedProject, setSelectedProject] = React.useState(null);
    const [projectDetails, setProjectDetails] = React.useState(null);

    const [showProjectModal, setShowProjectModal] = React.useState(false);
    const [showBudgetItemModal, setShowBudgetItemModal] = React.useState(false);

    const api = useApi();

    const fetchProjects = async () => {
        try {
            const response = await api.get('/api/construction/projects');
            setProjects(response.data || []);
        } catch (error) {
            console.error("Error fetching projects:", error);
            alert('Error al cargar los proyectos de construcción.');
        }
    };

    React.useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjectDetails = async (projectId) => {
        try {
            const response = await api.get(`/api/construction/projects/${projectId}`);
            setProjectDetails(response.data || null);
            setSelectedProject(projects.find(p => p.id === projectId));
        } catch (error) {
            console.error("Error fetching project details:", error);
            alert('Error al cargar los detalles del proyecto.');
        }
    };

    const handleCreateProject = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        try {
            await api.post('/api/construction/projects', data);
            setShowProjectModal(false);
            fetchProjects();
            alert('Proyecto de construcción creado con éxito.');
        } catch (error) {
            console.error("Error creating project:", error);
            alert('Error al crear el proyecto.');
        }
    };

    const handleAddBudgetItem = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        data.amount = parseFloat(data.amount);
        try {
            await api.post(`/api/construction/projects/${selectedProject.id}/budget_items`, data);
            setShowBudgetItemModal(false);
            fetchProjectDetails(selectedProject.id); // Refresh details
            alert('Partida presupuestaria agregada con éxito.');
        } catch (error) {
            console.error("Error adding budget item:", error);
            alert('Error al agregar la partida.');
        }
    };

    return (
        <div className="container-fluid">
            <h1>Gestión de Obras y Construcción (LAN-OBR5)</h1>
            <p>Presupuesto de obra, partidas, avance físico, certificaciones y pagos a contratistas.</p>

            <div className="row">
                <div className="col-md-4">
                    <div className="card">
                        <div className="card-header d-flex justify-content-between align-items-center">
                            Proyectos
                            <button className="btn btn-sm btn-primary" onClick={() => setShowProjectModal(true)}>+</button>
                        </div>
                        <ul className="list-group list-group-flush">
                            {projects.map(p => (
                                <li key={p.id} className={`list-group-item list-group-item-action ${selectedProject?.id === p.id ? 'active' : ''}`} onClick={() => fetchProjectDetails(p.id)}>
                                    {p.name} <span className="badge bg-secondary float-end">{p.status}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
                <div className="col-md-8">
                    {selectedProject ? (
                        <div className="card">
                            <div className="card-header">
                                <h3>Detalles de: {selectedProject.name}</h3>
                                <p><strong>Ubicación:</strong> {selectedProject.location || 'N/A'} | <strong>Presupuesto:</strong> ${selectedProject.budget?.toFixed(2) || '0.00'}</p>
                            </div>
                            <div className="card-body">
                                <h4>Partidas del Presupuesto <button className="btn btn-sm btn-outline-primary ms-2" onClick={() => setShowBudgetItemModal(true)}>+</button></h4>
                                <table className="table">
                                    <thead><tr><th>Código</th><th>Nombre</th><th className="text-end">Monto</th></tr></thead>
                                    <tbody>
                                        {projectDetails?.budget_items.map(item => (
                                            <tr key={item.id}>
                                                <td>{item.code}</td>
                                                <td>{item.name}</td>
                                                <td className="text-end">${item.amount.toFixed(2)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>

                                <h4 className="mt-4">RFIs (Request for Information)</h4>
                                {/* Placeholder for RFIs */}
                                <p>No hay RFIs para este proyecto.</p>

                                <h4 className="mt-4">Hitos de Facturación</h4>
                                {/* Placeholder for Milestones */}
                                <p>No hay hitos de facturación para este proyecto.</p>

                            </div>
                        </div>
                    ) : (
                        <div className="alert alert-info">Seleccione un proyecto para ver sus detalles.</div>
                    )}
                </div>
            </div>

            {/* Modal para nuevo proyecto */}
            {showProjectModal && (
                <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <form onSubmit={handleCreateProject}>
                                <div className="modal-header"><h5 className="modal-title">Nuevo Proyecto</h5><button type="button" className="btn-close" onClick={() => setShowProjectModal(false)}></button></div>
                                <div className="modal-body">
                                    <div className="mb-3"><label className="form-label">Nombre del Proyecto</label><input type="text" className="form-control" name="name" required /></div>
                                    <div className="mb-3"><label className="form-label">Ubicación</label><input type="text" className="form-control" name="location" /></div>
                                    <div className="mb-3"><label className="form-label">Fecha de Inicio</label><input type="date" className="form-control" name="start_date" /></div>
                                    <div className="mb-3"><label className="form-label">Presupuesto Total</label><input type="number" step="0.01" className="form-control" name="budget" /></div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowProjectModal(false)}>Cerrar</button>
                                    <button type="submit" className="btn btn-primary">Crear Proyecto</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal para nueva partida */}
            {showBudgetItemModal && selectedProject && (
                 <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <form onSubmit={handleAddBudgetItem}>
                                <div className="modal-header"><h5 className="modal-title">Nueva Partida para {selectedProject.name}</h5><button type="button" className="btn-close" onClick={() => setShowBudgetItemModal(false)}></button></div>
                                <div className="modal-body">
                                    <div className="mb-3"><label className="form-label">Código de Partida</label><input type="text" className="form-control" name="code" /></div>
                                    <div className="mb-3"><label className="form-label">Nombre de la Partida</label><input type="text" className="form-control" name="name" required /></div>
                                    <div className="mb-3"><label className="form-label">Monto</label><input type="number" step="0.01" className="form-control" name="amount" required /></div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowBudgetItemModal(false)}>Cerrar</button>
                                    <button type="submit" className="btn btn-primary">Agregar Partida</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
