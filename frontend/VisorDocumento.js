const VisorDocumento = () => {
    const [contenido, setContenido] = React.useState('');

    React.useEffect(() => {
        try {
            // En el futuro, esto se obtendría de la API: fetch(`/api/documento/${documentoId}`)
            const contenidoDeEjemplo = `
                <h2>CONTRATO DE PRÉSTAMO</h2>
                <p>
                    En la ciudad de San Salvador, a los 13 días del mes de octubre de 2025.
                </p>
                <p>
                    <strong>DE UNA PARTE:</strong> LAZOARCE NEXUS S.A. de C.V., en adelante "EL PRESTAMISTA".
                </p>
                <p>
                    <strong>DE OTRA PARTE:</strong> [Nombre del Cliente], en adelante "EL PRESTATARIO".
                </p>
                <p>
                    Ambas partes acuerdan un préstamo por la cantidad de <strong>$5,000.00 USD</strong>, bajo los siguientes términos y condiciones...
                </p>
                <p>
                    [...]
                </p>
                <p>
                    El PRESTATARIO se compromete a pagar el monto total más los intereses generados en un plazo de 24 meses.
                </p>
            `;
            setContenido(contenidoDeEjemplo);
        } catch (error) {
            console.error("Error en useEffect de VisorDocumento:", error);
        }
    }, []);

    return (
        <div>
            <h3>Documento a Firmar</h3>
            <div
                style={{
                    border: '1px solid #eee',
                    padding: '20px',
                    height: '400px',
                    overflowY: 'scroll',
                    backgroundColor: '#f9f9f9',
                    fontFamily: 'Arial, sans-serif'
                }}
                dangerouslySetInnerHTML={{ __html: contenido }}
            />
        </div>
    );
};