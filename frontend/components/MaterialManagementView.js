const MaterialManagementView = () => {
    const [materials, setMaterials] = React.useState([]);
    const [requests, setRequests] = React.useState([]);
    const [view, setView] = React.useState('requests'); // requests | inventory

    const [showMaterialModal, setShowMaterialModal] = React.useState(false);
    const [showRequestModal, setShowRequestModal] = React.useState(false);

    const api = useApi();

    const fetchData = async () => {
        try {
            const materialsResponse = await api.get('/api/materials/');
            setMaterials(materialsResponse.data || []);
            const requestsResponse = await api.get('/api/materials/requests');
            setRequests(requestsResponse.data || []);
        } catch (error) {
            console.error("Error fetching material data:", error);
            alert('Error al cargar los datos de materiales.');
        }
    };

    React.useEffect(() => {
        fetchData();
    }, []);

    const handleCreateMaterial = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        data.stock = parseInt(data.stock, 10) || 0;
        try {
            await api.post('/api/materials/', data);
            setShowMaterialModal(false);
            fetchData();
            alert('Material creado con éxito.');
        } catch (error) {
            console.error("Error creating material:", error);
            alert('Error al crear el material.');
        }
    };

    const handleCreateRequest = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        data.quantity = parseInt(data.quantity, 10);
        data.material_id = parseInt(data.material_id, 10);
        try {
            await api.post('/api/materials/requests', data);
            setShowRequestModal(false);
            fetchData();
            alert('Solicitud de material enviada.');
        } catch (error) {
            console.error("Error creating material request:", error);
            alert('Error al crear la solicitud.');
        }
    };

    const handleUpdateRequestStatus = async (requestId, newStatus) => {
        if (!confirm(`¿Está seguro de que desea cambiar el estado a "${newStatus}"?`)) return;

        try {
            await api.put(`/api/materials/requests/${requestId}/status`, { status: newStatus });
            fetchData();
            alert(`Solicitud ${newStatus.toLowerCase()} con éxito.`);
        } catch (error) {
            console.error(`Error updating request status:`, error);
            alert('Error al actualizar el estado de la solicitud.');
        }
    };

    const renderRequestsView = () => (
        <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
                Solicitudes de Materiales
                <button className="btn btn-sm btn-primary" onClick={() => setShowRequestModal(true)}>Nueva Solicitud</button>
            </div>
            <div className="card-body">
                <table className="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Solicitante</th>
                            <th>Material</th>
                            <th>Cantidad</th>
                            <th>Fecha</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {requests.map(req => (
                            <tr key={req.id}>
                                <td>{req.id}</td>
                                <td>{req.requester_name}</td>
                                <td>{req.material_name}</td>
                                <td>{req.quantity}</td>
                                <td>{new Date(req.created_at).toLocaleDateString()}</td>
                                <td><span className={`badge bg-info`}>{req.status}</span></td>
                                <td>
                                    {req.status === 'Pendiente' && (
                                        <>
                                            <button className="btn btn-sm btn-success me-1" onClick={() => handleUpdateRequestStatus(req.id, 'Aprobada')}>Aprobar</button>
                                            <button className="btn btn-sm btn-danger" onClick={() => handleUpdateRequestStatus(req.id, 'Rechazada')}>Rechazar</button>
                                        </>
                                    )}
                                    {req.status === 'Aprobada' && (
                                        <button className="btn btn-sm btn-primary" onClick={() => handleUpdateRequestStatus(req.id, 'Entregada')}>Marcar como Entregada</button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );

    const renderInventoryView = () => (
         <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
                Inventario de Materiales
                <button className="btn btn-sm btn-primary" onClick={() => setShowMaterialModal(true)}>Nuevo Material</button>
            </div>
            <div className="card-body">
                <table className="table table-striped">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Descripción</th>
                            <th>Stock</th>
                            <th>Unidad</th>
                        </tr>
                    </thead>
                    <tbody>
                        {materials.map(mat => (
                            <tr key={mat.id}>
                                <td>{mat.id}</td>
                                <td>{mat.name}</td>
                                <td>{mat.description}</td>
                                <td>{mat.stock}</td>
                                <td>{mat.unit}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );

    return (
        <div className="container-fluid">
            <h1>Recursos Materiales (LAN-RM1)</h1>
            <p>Solicitudes de materiales, aprobación, entrega y control de stock no valorado.</p>

            <ul className="nav nav-tabs">
                <li className="nav-item">
                    <a className={`nav-link ${view === 'requests' ? 'active' : ''}`} href="#" onClick={() => setView('requests')}>Solicitudes</a>
                </li>
                <li className="nav-item">
                    <a className={`nav-link ${view === 'inventory' ? 'active' : ''}`} href="#" onClick={() => setView('inventory')}>Inventario</a>
                </li>
            </ul>

            <div className="mt-3">
                {view === 'requests' ? renderRequestsView() : renderInventoryView()}
            </div>

            {/* Modal para nuevo material */}
            {showMaterialModal && (
                <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <form onSubmit={handleCreateMaterial}>
                                <div className="modal-header">
                                    <h5 className="modal-title">Nuevo Material</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowMaterialModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <div className="mb-3"><label className="form-label">Nombre</label><input type="text" className="form-control" name="name" required /></div>
                                    <div className="mb-3"><label className="form-label">Descripción</label><textarea className="form-control" name="description"></textarea></div>
                                    <div className="mb-3"><label className="form-label">Unidad (ej. Cajas)</label><input type="text" className="form-control" name="unit" /></div>
                                    <div className="mb-3"><label className="form-label">Stock Inicial</label><input type="number" className="form-control" name="stock" defaultValue="0" /></div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowMaterialModal(false)}>Cerrar</button>
                                    <button type="submit" className="btn btn-primary">Guardar</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal para nueva solicitud */}
            {showRequestModal && (
                <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <form onSubmit={handleCreateRequest}>
                                <div className="modal-header">
                                    <h5 className="modal-title">Nueva Solicitud de Material</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowRequestModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <div className="mb-3">
                                        <label className="form-label">Material</label>
                                        <select className="form-select" name="material_id" required>
                                            <option value="">Seleccione un material</option>
                                            {materials.map(m => <option key={m.id} value={m.id}>{m.name} (Stock: {m.stock})</option>)}
                                        </select>
                                    </div>
                                    <div className="mb-3"><label className="form-label">Cantidad</label><input type="number" className="form-control" name="quantity" required min="1" /></div>
                                    <div className="mb-3"><label className="form-label">Notas (Justificación)</label><textarea className="form-control" name="notes"></textarea></div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowRequestModal(false)}>Cerrar</button>
                                    <button type="submit" className="btn btn-primary">Enviar Solicitud</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
