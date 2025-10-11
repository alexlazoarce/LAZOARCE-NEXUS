const TestingView = ({ token }) => {
    const [message, setMessage] = React.useState('');
    const [error, setError] = React.useState('');
    const [loading, setLoading] = React.useState(false);

    const handleGenerateData = async () => {
        if (!window.confirm('Esto creará nuevos usuarios y préstamos en el sistema. ¿Está seguro?')) {
            return;
        }
        setLoading(true);
        setMessage('');
        setError('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/testing/generate-dummy-data`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Error al generar datos.');
            setMessage(data.message);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h3>Herramientas de Prueba Piloto</h3>
            <p>Use estas herramientas para generar datos ficticios y probar los flujos del sistema.</p>
            <div style={{border: '1px solid #ccc', padding: '10px'}}>
                <h4>Generador de Datos de Prueba</h4>
                <button onClick={handleGenerateData} disabled={loading}>
                    {loading ? 'Generando...' : 'Crear 1 Cliente, 1 Préstamo y 1 Pago'}
                </button>
                {message && <p style={{color: 'green'}}>{message}</p>}
                {error && <p style={{color: 'red'}}>{error}</p>}
            </div>
        </div>
    );
};