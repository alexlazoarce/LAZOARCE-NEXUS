// frontend/DocumentView.js

const DocumentView = () => {
    const [documents, setDocuments] = React.useState([]);
    const [selectedFile, setSelectedFile] = React.useState(null);
    const [description, setDescription] = React.useState('');
    const [uploading, setUploading] = React.useState(false);
    const [error, setError] = React.useState('');

    const fetchDocuments = () => {
        // En una implementación real, aquí se haría una llamada al backend
        // Para este placeholder, usamos datos de ejemplo.
        const mockDocuments = [
            { id: 1, filename: 'contrato_prestamo.pdf', description: 'Contrato inicial del préstamo #123', updated_at: '2023-10-26T10:00:00Z' },
            { id: 2, filename: 'identificacion_cliente.jpg', description: 'DUI del cliente', updated_at: '2023-10-25T15:30:00Z' },
        ];
        setDocuments(mockDocuments);
    };

    React.useEffect(() => {
        fetchDocuments();
    }, []);

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
    };

    const handleUpload = () => {
        if (!selectedFile) {
            setError('Por favor, seleccione un archivo.');
            return;
        }
        setUploading(true);
        setError('');

        // Simulación de la subida de un archivo
        console.log('Subiendo archivo:', selectedFile.name);
        console.log('Descripción:', description);

        setTimeout(() => {
            setUploading(false);
            // Aquí se debería volver a llamar a fetchDocuments() para actualizar la lista
            alert('Archivo subido (simulación).');
            setSelectedFile(null);
            setDescription('');
        }, 1500);
    };

    return (
        <div className="container">
            <h2>LAN-GD2: Gestor de Documentos</h2>

            <div className="card mb-4">
                <div className="card-header">Subir Nuevo Documento</div>
                <div className="card-body">
                    {error && <div className="alert alert-danger">{error}</div>}
                    <div className="form-group mb-3">
                        <label htmlFor="file-upload">Seleccionar Archivo</label>
                        <input type="file" className="form-control" id="file-upload" onChange={handleFileChange} />
                    </div>
                    <div className="form-group mb-3">
                        <label htmlFor="description">Descripción</label>
                        <input
                            type="text"
                            className="form-control"
                            id="description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Ej: DUI del cliente"
                        />
                    </div>
                    <button className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
                        {uploading ? 'Subiendo...' : 'Subir Documento'}
                    </button>
                </div>
            </div>

            <div className="card">
                <div className="card-header">Documentos Almacenados</div>
                <div className="card-body">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Nombre del Archivo</th>
                                <th>Descripción</th>
                                <th>Última Modificación</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {documents.map(doc => (
                                <tr key={doc.id}>
                                    <td>{doc.filename}</td>
                                    <td>{doc.description}</td>
                                    <td>{new Date(doc.updated_at).toLocaleString()}</td>
                                    <td>
                                        <button className="btn btn-sm btn-info me-2">Ver Versiones</button>
                                        <button className="btn btn-sm btn-success">Descargar</button>
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
