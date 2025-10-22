const TaxView = () => {
    // Estado para tipos de impuestos y declaraciones
    const [taxTypes, setTaxTypes] = React.useState([]);
    const [declarations, setDeclarations] = React.useState([]);

    // Estado para modales
    const [showTaxTypeModal, setShowTaxTypeModal] = React.useState(false);
    const [showDeclarationModal, setShowDeclarationModal] = React.useState(false);
    const [editingTaxType, setEditingTaxType] = React.useState(null);

    const api = useApi();

    const fetchTaxTypes = async () => {
        try {
            const response = await api.get('/api/tax/types');
            setTaxTypes(response.data || []);
        } catch (error) {
            console.error("Error fetching tax types:", error);
            alert('Error al cargar los tipos de impuesto.');
        }
    };

    const fetchDeclarations = async () => {
        try {
            const response = await api.get('/api/tax/declarations');
            setDeclarations(response.data || []);
        } catch (error) {
            console.error("Error fetching declarations:", error);
            alert('Error al cargar las declaraciones.');
        }
    };

    React.useEffect(() => {
        fetchTaxTypes();
        fetchDeclarations();
    }, []);

    const handleTaxTypeSubmit = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        data.rate = parseFloat(data.rate);

        try {
            if (editingTaxType) {
                await api.put(`/api/tax/types/${editingTaxType.id}`, data);
                alert('Tipo de impuesto actualizado con éxito.');
            } else {
                await api.post('/api/tax/types', data);
                alert('Tipo de impuesto creado con éxito.');
            }
            setShowTaxTypeModal(false);
            setEditingTaxType(null);
            fetchTaxTypes();
        } catch (error) {
            console.error("Error saving tax type:", error);
            alert('Error al guardar el tipo de impuesto.');
        }
    };

    const handleGenerateDeclaration = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        try {
            await api.post('/api/tax/declarations/iva', data);
            setShowDeclarationModal(false);
            fetchDeclarations();
            alert('Declaración de IVA generada con éxito.');
        } catch (error) {
            console.error("Error generating IVA declaration:", error);
            alert('Error al generar la declaración de IVA.');
        }
    };

    const openEditModal = (taxType) => {
        setEditingTaxType(taxType);
        setShowTaxTypeModal(true);
    };

    const openNewModal = () => {
        setEditingTaxType(null);
        setShowTaxTypeModal(true);
    };


    return (
        <div className="container-fluid">
            <h1>Gestión de Impuestos (LAN-TAX1)</h1>
            <p>Este módulo calcula automáticamente IVA, retenciones y genera declaraciones prellenadas.</p>

            <div className="row">
                <div className="col-md-6">
                    <div className="card">
                        <div className="card-header d-flex justify-content-between align-items-center">
                            Tipos de Impuesto
                            <button className="btn btn-sm btn-primary" onClick={openNewModal}>+</button>
                        </div>
                        <div className="card-body">
                            <table className="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Nombre</th>
                                        <th>Tasa (%)</th>
                                        <th>País</th>
                                        <th>Categoría</th>
                                        <th>Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {taxTypes.map(tt => (
                                        <tr key={tt.id}>
                                            <td>{tt.name}</td>
                                            <td>{tt.rate}</td>
                                            <td>{tt.country_code}</td>
                                            <td>{tt.tax_category}</td>
                                            <td>
                                                <button className="btn btn-sm btn-secondary" onClick={() => openEditModal(tt)}>Editar</button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div className="col-md-6">
                     <div className="card">
                        <div className="card-header d-flex justify-content-between align-items-center">
                            Declaraciones Generadas
                            <button className="btn btn-sm btn-success" onClick={() => setShowDeclarationModal(true)}>Generar IVA Mensual</button>
                        </div>
                        <div className="card-body">
                            <ul className="list-group">
                                {declarations.map(d => (
                                    <li key={d.id} className="list-group-item">
                                        <strong>{d.declaration_type}</strong> ({d.period_start} a {d.period_end})
                                        <br/>
                                        <small>Impuesto a pagar: ${d.calculated_data?.impuesto_resultante?.toFixed(2) || 'N/A'}</small>
                                        <span className={`badge bg-${d.status === 'Borrador' ? 'warning' : 'success'} float-end`}>{d.status}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            {/* Modal para Tipos de Impuesto */}
            {showTaxTypeModal && (
                <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <form onSubmit={handleTaxTypeSubmit}>
                                <div className="modal-header">
                                    <h5 className="modal-title">{editingTaxType ? 'Editar' : 'Nuevo'} Tipo de Impuesto</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowTaxTypeModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <div className="mb-3">
                                        <label htmlFor="name" className="form-label">Nombre</label>
                                        <input type="text" className="form-control" name="name" defaultValue={editingTaxType?.name || ''} required />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="rate" className="form-label">Tasa (%)</label>
                                        <input type="number" step="0.01" className="form-control" name="rate" defaultValue={editingTaxType?.rate || ''} required />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="country_code" className="form-label">Código de País (ej. SV)</label>
                                        <input type="text" className="form-control" name="country_code" defaultValue={editingTaxType?.country_code || ''} required />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="tax_category" className="form-label">Categoría</label>
                                        <select className="form-select" name="tax_category" defaultValue={editingTaxType?.tax_category || 'IVA'}>
                                            <option value="IVA">IVA</option>
                                            <option value="Retencion">Retención</option>
                                            <option value="Otro">Otro</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowTaxTypeModal(false)}>Cerrar</button>
                                    <button type="submit" className="btn btn-primary">Guardar</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal para Generar Declaración */}
            {showDeclarationModal && (
                 <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <form onSubmit={handleGenerateDeclaration}>
                                <div className="modal-header">
                                    <h5 className="modal-title">Generar Declaración de IVA</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowDeclarationModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <p>Seleccione el periodo para el cálculo automático del IVA.</p>
                                    <div className="mb-3">
                                        <label htmlFor="start_date" className="form-label">Fecha de Inicio</label>
                                        <input type="date" className="form-control" name="start_date" required />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="end_date" className="form-label">Fecha de Fin</label>
                                        <input type="date" className="form-control" name="end_date" required />
                                    </div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowDeclarationModal(false)}>Cerrar</button>
                                    <button type="submit" className="btn btn-primary">Generar</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
