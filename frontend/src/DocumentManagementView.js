// frontend/src/DocumentManagementView.js

const DocumentManagementView = () => {
    const [documents, setDocuments] = React.useState([]);
    const [selectedFile, setSelectedFile] = React.useState(null);
    const [description, setDescription] = React.useState('');
    const [error, setError] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);
    const [uploadTarget, setUploadTarget] = React.useState({ type: 'new', docId: null }); // 'new' or 'version'

    const apiBaseUrl = 'http://127.0.0.1:5001/api';

    const getAuthToken = () => localStorage.getItem('accessToken');

    const fetchDocuments = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`${apiBaseUrl}/documents`, {
                headers: { 'Authorization': `Bearer ${getAuthToken()}` }
            });
            if (!response.ok) {
                throw new Error('No se pudieron cargar los documentos. Verifique su suscripción al módulo LAN-GD2.');
            }
            const data = await response.json();
            // Simple sort to show newest first
            data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            setDocuments(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    React.useEffect(() => {
        fetchDocuments();
    }, []);

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setError('Por favor, seleccione un archivo.');
            return;
        }

        setIsLoading(true);
        setError('');

        const formData = new FormData();
        formData.append('file', selectedFile);

        let url = `${apiBaseUrl}/documents/upload`;
        if (uploadTarget.type === 'version' && uploadTarget.docId) {
            url = `${apiBaseUrl}/documents/${uploadTarget.docId}/upload_version`;
        } else {
             formData.append('description', description);
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${getAuthToken()}` },
                body: formData,
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Falló la subida del archivo.');
            }

            // Reset form and refresh list
            setSelectedFile(null);
            setDescription('');
            document.getElementById('file-input').value = null; // Clear file input
            setUploadTarget({ type: 'new', docId: null });
            fetchDocuments(); // Refresh the document list

        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    // This is a simplified download handler. A robust solution would handle blobs and create a download link.
    const handleDownload = async (versionId, filename) => {
        try {
            const response = await fetch(`${apiBaseUrl}/documents/download/${versionId}`, {
                headers: { 'Authorization': `Bearer ${getAuthToken()}` }
            });

            if (!response.ok) {
                 const errData = await response.json();
                throw new Error(errData.error || 'No se pudo descargar el archivo.');
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', filename); // Use the original filename
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);

        } catch (err) {
            setError(err.message);
        }
    };

    const prepareNewVersionUpload = (docId) => {
        setUploadTarget({ type: 'version', docId: docId });
        setError(`Listo para subir una nueva versión para el Documento ID: ${docId}. Seleccione un archivo y presione "Subir Archivo".`);
        document.getElementById('file-input').click(); // Prompt user to select file
    };


    return React.createElement('div', { className: 'container mt-4' },
        React.createElement('h2', { className: 'text-center mb-4', style: { color: '#1a365d' } }, 'Gestor de Documentos (LAN-GD2)'),

        isLoading && React.createElement('p', null, 'Cargando...'),
        error && React.createElement('div', { className: 'alert alert-danger' }, error),

        // Upload Section
        React.createElement('div', { className: 'card mb-4' },
            React.createElement('div', { className: 'card-body' },
                React.createElement('h5', { className: 'card-title' }, uploadTarget.type === 'new' ? 'Subir Nuevo Documento' : `Subir Nueva Versión para Doc #${uploadTarget.docId}`),
                React.createElement('div', { className: 'mb-3' },
                    React.createElement('input', { type: 'file', id: 'file-input', className: 'form-control', onChange: handleFileChange })
                ),
                uploadTarget.type === 'new' && React.createElement('div', { className: 'mb-3' },
                    React.createElement('label', { htmlFor: 'description', className: 'form-label' }, 'Descripción (Opcional)'),
                    React.createElement('input', {
                        type: 'text',
                        id: 'description',
                        className: 'form-control',
                        value: description,
                        onChange: (e) => setDescription(e.target.value)
                    })
                ),
                React.createElement('button', {
                    className: 'btn',
                    style: { backgroundColor: '#059669', color: 'white' },
                    onClick: handleUpload,
                    disabled: isLoading || !selectedFile
                }, isLoading ? 'Subiendo...' : 'Subir Archivo'),
                uploadTarget.type === 'version' && React.createElement('button', {
                    className: 'btn btn-secondary ms-2',
                    onClick: () => { setUploadTarget({ type: 'new', docId: null }); setError(''); }
                }, 'Cancelar Subida de Versión')
            )
        ),

        // Document List Section
        React.createElement('div', { className: 'card' },
            React.createElement('div', { className: 'card-body' },
                React.createElement('h5', { className: 'card-title' }, 'Repositorio de Documentos'),
                React.createElement('table', { className: 'table' },
                    React.createElement('thead', null,
                        React.createElement('tr', null,
                            React.createElement('th', null, 'Nombre de Archivo'),
                            React.createElement('th', null, 'Descripción'),
                            React.createElement('th', null, 'Fecha de Creación'),
                            React.createElement('th', null, 'Acciones')
                        )
                    ),
                    React.createElement('tbody', null,
                        documents.map(doc => React.createElement('tr', { key: doc.id },
                            React.createElement('td', null, doc.filename),
                            React.createElement('td', null, doc.description),
                            React.createElement('td', null, new Date(doc.created_at).toLocaleString()),
                            React.createElement('td', null,
                                // In a real app, you would fetch and list versions.
                                // For simplicity, we assume the latest version is the one to download.
                                // We need a way to get the latest version ID from the backend.
                                // Let's pretend the service needs to be updated for this.
                                // For now, we'll just have a button to upload a new version.
                                 React.createElement('button', {
                                    className: 'btn btn-sm btn-primary me-2',
                                    onClick: () => handleDownload(doc.latest_version_id, doc.filename) // Assuming a 'latest_version_id' field
                                 }, 'Descargar'),
                                React.createElement('button', {
                                    className: 'btn btn-sm',
                                    style: { backgroundColor: '#1a365d', color: 'white' },
                                    onClick: () => prepareNewVersionUpload(doc.id)
                                }, 'Subir Versión')
                            )
                        ))
                    )
                )
            )
        )
    );
};
