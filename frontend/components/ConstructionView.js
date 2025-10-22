const ConstructionView = () => {
    const [projects, setProjects] = React.useState([]);
    const [selectedProject, setSelectedProject] = React.useState(null);
    const [projectDetails, setProjectDetails] = React.useState(null);

    const [showProjectModal, setShowProjectModal] = React.useState(false);
    const [showBudgetItemModal, setShowBudgetItemModal] = React.useState(false);

    // Assuming useApi() is a custom hook providing an configured axios instance or similar
    const api = useApi();

    // Fetch the list of construction projects
    const fetchProjects = async () => {
        try {
            const response = await api.get('/api/construction/projects');
            setProjects(response.data || []); // Ensure projects is always an array
        } catch (error) {
            console.error("Error fetching projects:", error);
            alert('Error al cargar los proyectos de construcción.');
        }
    };

    // Fetch projects when the component mounts
    React.useEffect(() => {
        fetchProjects();
        // The dependency array is empty, so this runs once on mount
    }, []);

    // Fetch detailed information for a selected project
    const fetchProjectDetails = async (projectId) => {
        // Find the project object from the already fetched list to update selectedProject state
        const projectFromList = projects.find(p => p.id === projectId);
        if (!projectFromList) return; // Should not happen if clicking on a list item

        setSelectedProject(projectFromList); // Set basic info immediately for responsiveness

        try {
            const response = await api.get(`/api/construction/projects/${projectId}`);
            setProjectDetails(response.data || null); // Update with full details
        } catch (error) {
            console.error("Error fetching project details:", error);
            alert('Error al cargar los detalles del proyecto.');
            setProjectDetails(null); // Clear details on error
        }
    };

    // Handle the submission of the new project form
    const handleCreateProject = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        // Basic validation/formatting (could be more robust)
        if (!data.name) {
            alert('El nombre del proyecto es obligatorio.');
            return;
        }
        data.budget = data.budget ? parseFloat(data.budget) : 0.0;

        try {
            await api.post('/api/construction/projects', data);
            setShowProjectModal(false); // Close modal on success
            fetchProjects(); // Refresh the project list
            alert('Proyecto de construcción creado con éxito.');
        } catch (error) {
            console.error("Error creating project:", error);
            // Provide more specific error if available from API response
            const errorMsg = error.response?.data?.error || 'Error al crear el proyecto.';
            alert(errorMsg);
        }
    };

    // Handle the submission of the new budget item form
    const handleAddBudgetItem = async (event) => {
        event.preventDefault();
        if (!selectedProject) return; // Should not happen if modal is shown correctly

        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        // Basic validation/formatting
        if (!data.name || !data.amount) {
            alert('El nombre y el monto de la partida son obligatorios.');
            return;
        }
        data.amount = parseFloat(data.amount);
        if (isNaN(data.amount)) {
             alert('El monto debe ser un número válido.');
             return;
        }


        try {
            await api.post(`/api/construction/projects/${selectedProject.id}/budget_items`, data);
            setShowBudgetItemModal(false); // Close modal on success
            fetchProjectDetails(selectedProject.id); // Refresh details to show the new item
            alert('Partida presupuestaria agregada con éxito.');
        } catch (error) {
            console.error("Error adding budget item:", error);
            const errorMsg = error.response?.data?.error || 'Error al agregar la partida.';
            alert(errorMsg);
        }
    };

    // --- Add handlers for Progress Reports, Certifications, RFIs, Milestones similarly ---
    // Example: const handleAddProgressReport = async (event) => { ... };
    // Example: const handleCreateRFI = async (event) => { ... };


    return (
        <div className="container-fluid"> {/* Using Bootstrap class */}
            <h1>Gestión de Obras y Construcción (LAN-OBR5)</h1>
            <p>Presupuesto de obra, partidas, avance físico, certificaciones y pagos a contratistas.</p>

            <div className="row"> {/* Bootstrap row */}
                {/* Project List Column */}
                <div className="col-md-4"> {/* Bootstrap column */}
                    <div className="card"> {/* Bootstrap card */}
                        <div className="card-header d-flex justify-content-between align-items-center">
                            Proyectos
                            {/* Button to open the new project modal */}
                            <button className="btn btn-sm btn-primary" onClick={() => setShowProjectModal(true)}>+</button>
                        </div>
                        <ul className="list-group list-group-flush">
                            {/* Render list of projects */}
                            {projects.length === 0 && <li className="list-group-item">No hay proyectos.</li>}
                            {projects.map(p => (
                                <li
                                    key={p.id}
                                    className={`list-group-item list-group-item-action ${selectedProject?.id === p.id ? 'active' : ''}`}
                                    onClick={() => fetchProjectDetails(p.id)} // Fetch details when a project is clicked
                                    style={{ cursor: 'pointer' }} // Indicate clickability
                                >
                                    {p.name}
                                    {/* Display project status */}
                                    <span className={`badge float-end ${p.status === 'Completado' ? 'bg-success' : 'bg-secondary'}`}>{p.status}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Project Details Column */}
                <div className="col-md-8">
                    {selectedProject ? (
                        <div className="card">
                            <div className="card-header">
                                <h3>Detalles de: {selectedProject.name}</h3>
                                {/* Display basic project info */}
                                <p>
                                    <strong>Ubicación:</strong> {selectedProject.location || 'N/A'} |{' '}
                                    <strong>Presupuesto:</strong> ${selectedProject.budget?.toFixed(2) || '0.00'} |{' '}
                                    <strong>Estado:</strong> {selectedProject.status}
                                </p>
                            </div>
                            <div className="card-body">
                                {/* Budget Items Section */}
                                <h4>
                                    Partidas del Presupuesto
                                    {/* Button to open the add budget item modal */}
                                    <button className="btn btn-sm btn-outline-primary ms-2" onClick={() => setShowBudgetItemModal(true)}>+</button>
                                </h4>
                                <table className="table table-sm"> {/* Bootstrap table */}
                                    <thead>
                                        <tr>
                                            <th>Código</th>
                                            <th>Nombre</th>
                                            <th className="text-end">Monto</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {/* Render budget items from projectDetails */}
                                        {projectDetails?.budget_items && projectDetails.budget_items.length > 0 ? (
                                            projectDetails.budget_items.map(item => (
                                                <tr key={item.id}>
                                                    <td>{item.code || '-'}</td>
                                                    <td>{item.name}</td>
                                                    <td className="text-end">${item.amount.toFixed(2)}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr><td colSpan="3">No hay partidas presupuestarias.</td></tr>
                                        )}
                                    </tbody>
                                </table>

                                {/* --- Sections for Progress Reports, Certifications, RFIs, Milestones --- */}
                                {/* Add tables/lists similar to Budget Items, using projectDetails data */}

                                <h4 className="mt-4">Reportes de Avance</h4>
                                {/* Placeholder - Implement table/list using projectDetails?.progress_reports */}
                                <p>No hay reportes de avance registrados.</p>

                                <h4 className="mt-4">Certificaciones</h4>
                                {/* Placeholder - Implement table/list using projectDetails?.certifications */}
                                <p>No hay certificaciones registradas.</p>

                                <h4 className="mt-4">RFIs (Request for Information)</h4>
                                {/* Placeholder - Implement table/list using projectDetails?.rfis */}
                                <p>No hay RFIs para este proyecto.</p>

                                <h4 className="mt-4">Hitos de Facturación</h4>
                                {/* Placeholder - Implement table/list using projectDetails?.milestones */}
                                <p>No hay hitos de facturación para este proyecto.</p>

                            </div> {/* End card-body */}
                        </div> /* End card */
                    ) : (
                        /* Message shown when no project is selected */
                        <div className="alert alert-info">Seleccione un proyecto para ver sus detalles.</div>
                    )}
                </div> {/* End col-md-8 */}
            </div> {/* End row */}

            {/* --- Modals --- */}

            {/* Modal for creating a new project */}
            {showProjectModal && (
                <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <form onSubmit={handleCreateProject}>
                                <div className="modal-header">
                                    <h5 className="modal-title">Nuevo Proyecto</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowProjectModal(false)} aria-label="Close"></button>
                                </div>
                                <div className="modal-body">
                                    <div className="mb-3">
                                        <label htmlFor="projectName" className="form-label">Nombre del Proyecto</label>
                                        <input type="text" className="form-control" id="projectName" name="name" required />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="projectLocation" className="form-label">Ubicación</label>
                                        <input type="text" className="form-control" id="projectLocation" name="location" />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="projectStartDate" className="form-label">Fecha de Inicio</label>
                                        <input type="date" className="form-control" id="projectStartDate" name="start_date" />
                                    </div>
                                     <div className="mb-3">
                                        <label htmlFor="projectEndDate" className="form-label">Fecha de Fin (Estimada)</label>
                                        <input type="date" className="form-control" id="projectEndDate" name="end_date" />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="projectBudget" className="form-label">Presupuesto Total</label>
                                        <input type="number" step="0.01" className="form-control" id="projectBudget" name="budget" placeholder="0.00"/>
                                    </div>
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

            {/* Modal for adding a new budget item */}
            {showBudgetItemModal && selectedProject && (
                 <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <form onSubmit={handleAddBudgetItem}>
                                <div className="modal-header">
                                    <h5 className="modal-title">Nueva Partida para {selectedProject.name}</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowBudgetItemModal(false)} aria-label="Close"></button>
                                </div>
                                <div className="modal-body">
                                    <div className="mb-3">
                                        <label htmlFor="itemCode" className="form-label">Código de Partida</label>
                                        <input type="text" className="form-control" id="itemCode" name="code" />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="itemName" className="form-label">Nombre de la Partida</label>
                                        <input type="text" className="form-control" id="itemName" name="name" required />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="itemAmount" className="form-label">Monto</label>
                                        <input type="number" step="0.01" className="form-control" id="itemAmount" name="amount" required placeholder="0.00"/>
                                    </div>
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

             {/* Add Modals for Progress Report, Certification, RFI, Milestone similarly */}

        </div> /* End container-fluid */
    );
};