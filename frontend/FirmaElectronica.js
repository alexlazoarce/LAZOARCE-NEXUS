const FirmaElectronica = ({ onFirmaChange }) => {
    const sigCanvas = React.useRef({});

    const limpiar = () => {
        sigCanvas.current.clear();
        onFirmaChange(null);
    };

    const guardar = () => {
        const dataURL = sigCanvas.current.getTrimmedCanvas().toDataURL('image/png');
        onFirmaChange(dataURL);
    };

    // Since the library is loaded via a script tag, it should be available as a global.
    // We need to ensure this component renders after the script has loaded.
    if (typeof ReactSignatureCanvas === 'undefined') {
        return <p>Cargando componente de firma...</p>;
    }

    return (
        <div>
            <h4>Firma Electrónica</h4>
            <div style={{ border: '1px solid #ccc', borderRadius: '5px' }}>
                <ReactSignatureCanvas
                    ref={sigCanvas}
                    penColor='black'
                    canvasProps={{width: 500, height: 200, className: 'sigCanvas'}}
                    onEnd={guardar}
                />
            </div>
            <button onClick={limpiar} style={{marginTop: '10px'}}>Limpiar Firma</button>
        </div>
    );
};