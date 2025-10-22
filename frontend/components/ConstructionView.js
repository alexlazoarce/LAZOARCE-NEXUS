import React from 'react';

// Asumiendo que useApi() es un hook personalizado que provee una instancia configurada de axios o similar
// import useApi from './useApi'; // Ejemplo de importación

const ConstructionView = () => {
    const [projects, setProjects] = React.useState([]);
    const [selectedProject, setSelectedProject] = React.useState(null);
    const [projectDetails, setProjectDetails] = React.useState(null);

    const [showProjectModal, setShowProjectModal] = React.useState(false);
    const [showBudgetItemModal, setShowBudgetItemModal] = React.useState(false);

    // Asumiendo que useApi() es un hook personalizado que provee una instancia configurada de axios o similar
    const api = useApi();

    // Obtener la lista de proyectos de construcción
    const fetchProjects = async () => {
        try {
            const response = await api.get('/api/construction/projects');
            setProjects(response.data || []); // Asegura que projects sea siempre un array
        } catch (error) {
            console.error("Error fetching projects:", error);
            alert('Error al cargar los proyectos de construcción.');
        }
    };

    // Obtener proyectos cuando el componente se monta
    React.useEffect(() => {
        fetchProjects();
        // El array de dependencias está vacío, así que esto se ejecuta una vez al montar
    }, []);

    // Obtener información detallada de un proyecto seleccionado
    const fetchProjectDetails = async (projectId) => {
        // Encuentra el objeto del proyecto en la lista ya obtenida para actualizar el estado selectedProject
        const projectFromList = projects.find(p => p.id === projectId);
        if (!projectFromList) return; // No debería pasar si se hace clic en un elemento de la lista

        setSelectedProject(projectFromList); // Establece la info básica inmediatamente para mejorar la respuesta

        try {
            const response = await api.get(`/api/construction/projects/${projectId}`);
            setProjectDetails(response.data || null); // Actualiza con los detalles completos
        } catch (error) {
            console.error("Error fetching project details:", error);
            alert('Error al cargar los detalles del proyecto.');
            setProjectDetails(null); // Limpia los detalles en caso de error
        }
    };

    // Manejar el envío del formulario de nuevo proyecto
    const handleCreateProject = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        // Validación/formateo básico (podría ser más robusto)
        if (!data.name) {
            alert('El nombre del proyecto es obligatorio.');
            return;
        }
        data.budget = data.budget ? parseFloat(data.budget) : 0.0;

        try {
            await api.post('/api/construction/projects', data);
            setShowProjectModal(false); // Cierra el modal si tiene éxito
            fetchProjects(); // Refresca la lista de proyectos
            alert('Proyecto de construcción creado con éxito.');
        } catch (error) {
            console.error("Error creating project:", error);
            // Provee un error más específico si está disponible en la respuesta de la API
            const errorMsg = error.response?.data?.error || 'Error al crear el proyecto.';
            alert(errorMsg);
        }
    };

    // Manejar el envío del formulario de nueva partida presupuestaria
    const handleAddBudgetItem = async (event) => {
        event.preventDefault();
        if (!selectedProject) return; // No debería pasar si el modal se muestra correctamente

        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        // Validación/formateo básico
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
            setShowBudgetItemModal(false); // Cierra el modal si tiene éxito
            fetchProjectDetails(selectedProject.id); // Refresca los detalles para mostrar el nuevo ítem
            alert('Partida presupuestaria agregada con éxito.');
        } catch (error) {
            console.error("Error adding budget item:", error);
            const errorMsg = error.response?.data?.error || 'Error al agregar la partida.';
            alert(errorMsg);
        }
    };

    // --- Añadir manejadores para Reportes de Avance, Certificaciones, RFIs, Hitos de forma similar ---
    // Ejemplo: const handleAddProgressReport = async (event) => { ... };
    // Ejemplo: const handleCreateRFI = async (event) => { ... };


    return (
        <div className="container-fluid"> {/* Usando clase Bootstrap */}
            <h1>Gestión de Obras y Construcción (LAN-OBR5)</h1>
            <p>Presupuesto de obra, partidas, avance físico, certificaciones y pagos a contratistas.</p>

            <div className="row"> {/* Fila Bootstrap */}
                {/* Columna Lista de Proyectos */}
                <div className="col-md-4"> {/* Columna Bootstrap */}
                    <div className="card"> {/* Tarjeta Bootstrap */}
                        <div className="card-header d-flex justify-content-between align-items-center">
                            Proyectos
                            {/* Botón para abrir el modal de nuevo proyecto */}
                            <button className="btn btn-sm btn-primary" onClick={() => setShowProjectModal(true)}>+</button>
                        </div>
                        <ul className="list-group list-group-flush">
                            {/* Renderizar lista de proyectos */}
                            {projects.length === 0 && <li className="list-group-item">No hay proyectos.</li>}
                            {projects.map(p => (
                                <li
                                    key={p.id}
                                    className={`list-group-item list-group-item-action ${selectedProject?.id === p.id ? 'active' : ''}`}
                                    onClick={() => fetchProjectDetails(p.id)} // Obtener detalles al hacer clic
                                    style={{ cursor: 'pointer' }} // Indica que se puede hacer clic
                                >
                                    {p.name}
                                    {/* Mostrar estado del proyecto */}
                                    <span className={`badge float-end ${p.status === 'Completado' ? 'bg-success' : 'bg-secondary'}`}>{p.status}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Columna Detalles del Proyecto */}
                <div className="col-md-8">
                    {selectedProject ? (
                        <div className="card">
                            <div className="card-header">
                                <h3>Detalles de: {selectedProject.name}</h3>
                                {/* Mostrar información básica del proyecto */}
                                <p>
                                    <strong>Ubicación:</strong> {selectedProject.location || 'N/A'} |{' '}
                                    <strong>Presupuesto:</strong> ${selectedProject.budget?.toFixed(2) || '0.00'} |{' '}
                                    <strong>Estado:</strong> {selectedProject.status}
                                </p>
                            </div>
                            <div className="card-body">
                                {/* Sección Partidas Presupuestarias */}
                                <h4>
                                    Partidas del Presupuesto
                                    {/* Botón para abrir el modal de agregar partida */}
                                    <button className="btn btn-sm btn-outline-primary ms-2" onClick={() => setShowBudgetItemModal(true)}>+</button>
                                </h4>
                                <table className="table table-sm"> {/* Tabla Bootstrap */}
                                    <thead>
                                        <tr>
                                            <th>Código</th>
                                            <th>Nombre</th>
                                            <th className="text-end">Monto</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {/* Renderizar partidas desde projectDetails */}
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

                                {/* --- Secciones para Reportes de Avance, Certificaciones, RFIs, Hitos --- */}
                                {/* Añadir tablas/listas similares a Partidas Presupuestarias, usando datos de projectDetails */}

                                <h4 className="mt-4">Reportes de Avance</h4>
                                {/* Placeholder - Implementar tabla/lista usando projectDetails?.progress_reports */}
                                <p>No hay reportes de avance registrados.</p>

                                <h4 className="mt-4">Certificaciones</h4>
                                {/* Placeholder - Implementar tabla/lista usando projectDetails?.certifications */}
                                <p>No hay certificaciones registradas.</p>

                                <h4 className="mt-4">RFIs (Request for Information)</h4>
                                {/* Placeholder - Implementar tabla/lista usando projectDetails?.rfis */}
                                <p>No hay RFIs para este proyecto.</p>

                                <h4 className="mt-4">Hitos de Facturación</h4>
                                {/* Placeholder - Implementar tabla/lista usando projectDetails?.milestones */}
                                <p>No hay hitos de facturación para este proyecto.</p>

                            </div> {/* Fin card-body */}
                        </div> /* Fin card */
                    ) : (
                        /* Mensaje mostrado cuando no hay proyecto seleccionado */
                        <div className="alert alert-info">Seleccione un proyecto para ver sus detalles.</div>
                    )}
                </div> {/* Fin col-md-8 */}
            </div> {/* Fin row */}

            {/* --- Modales --- */}

            {/* Modal para crear un nuevo proyecto */}
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

            {/* Modal para añadir una nueva partida presupuestaria */}
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

             {/* Añadir Modales para Reporte de Avance, Certificación, RFI, Hito de forma similar */}

        </div> /* Fin container-fluid */
    );
};

// Asumiendo que exportas el componente si estás usando módulos ES6
// export default ConstructionView;