const PaginaFirma = () => {
    const [firmaDataUrl, setFirmaDataUrl] = React.useState(null);

    const handleFirmaChange = (dataUrl) => {
        setFirmaDataUrl(dataUrl);
    };

    const handleFirmarDocumento = () => {
        if (!firmaDataUrl) {
            alert('Por favor, estampe su firma antes de continuar.');
            return;
        }
        console.log("Documento Firmado con la siguiente firma:");
        console.log(firmaDataUrl);
        // En el futuro, aquí se haría la llamada a la API:
        // fetch('/api/documentos/firmar', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({ documentoId: '123', firma: firmaDataUrl })
        // });
        alert('¡Documento firmado con éxito! (Simulación)');
    };

    return (
        <div style={{ padding: '20px' }}>
            <h1>Firma de Contrato - NEXUS FEV</h1>
            <p>Por favor, revise el siguiente documento y estampe su firma electrónica en el recuadro correspondiente.</p>
            <hr />
            <VisorDocumento />
            <br />
            <FirmaElectronica onFirmaChange={handleFirmaChange} />
            <br />
            <button
                onClick={handleFirmarDocumento}
                disabled={!firmaDataUrl}
                style={{
                    padding: '10px 20px',
                    fontSize: '16px',
                    backgroundColor: firmaDataUrl ? 'green' : 'grey',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer'
                }}
            >
                Firmar y Aceptar Contrato
            </button>
        </div>
    );
};