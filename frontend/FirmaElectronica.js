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

    return (
        <div>
            <h4>Firma Electrónica</h4>
            <div style={{ border: '1px solid #ccc', borderRadius: '5px' }}>
                {React.createElement(window.ReactSignatureCanvas, {
                    ref: sigCanvas,
                    penColor: 'black',
                    canvasProps: {width: 500, height: 200, className: 'sigCanvas'},
                    onEnd: guardar
                })}
            </div>
            <button onClick={limpiar} style={{marginTop: '10px'}}>Limpiar Firma</button>
        </div>
    );
};