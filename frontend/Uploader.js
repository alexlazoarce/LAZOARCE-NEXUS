const Uploader = () => {

    const handleUploadClick = () => {
        // En una implementación real, esto abriría un input de tipo 'file'
        // o usaría una librería de drag-and-drop.
        alert('Simulando apertura de diálogo para subir archivo...');
    };

    const buttonStyle = {
        backgroundColor: '#007bff',
        color: 'white',
        padding: '10px 20px',
        border: 'none',
        borderRadius: '5px',
        cursor: 'pointer',
        fontSize: '16px',
        margin: '10px 0'
    };

    return (
        <div>
            <button onClick={handleUploadClick} style={buttonStyle}>
                Subir Archivo
            </button>
        </div>
    );
};