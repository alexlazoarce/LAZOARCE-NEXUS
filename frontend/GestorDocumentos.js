const GestorDocumentos = () => {

    const pageStyle = {
        padding: '20px',
        fontFamily: 'Arial, sans-serif'
    };

    const headerStyle = {
        borderBottom: '2px solid #eee',
        paddingBottom: '10px',
        marginBottom: '20px'
    };

    return (
        <div style={pageStyle}>
            <div style={headerStyle}>
                <h1>Gestor de Documentos - NEXUS G2D</h1>
                <p>Centralice y gestione todos sus archivos importantes.</p>
            </div>

            <Uploader />

            <ListaArchivos />
        </div>
    );
};