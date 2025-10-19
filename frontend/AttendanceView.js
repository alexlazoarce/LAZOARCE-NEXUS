const AttendanceView = ({ token }) => {
    const [qrToken, setQrToken] = React.useState('');
    const [history, setHistory] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    const fetchData = async () => {
        try {
            setLoading(true);
            const [tokenRes, historyRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/attendance/my-qr-token`, { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/api/attendance/my-history`, { headers: { 'Authorization': `Bearer ${token}` } })
            ]);
            if (!tokenRes.ok) throw new Error('No se pudo cargar tu código QR.');
            if (!historyRes.ok) throw new Error('No se pudo cargar tu historial de asistencia.');

            const tokenData = await tokenRes.json();
            const historyData = await historyRes.json();

            setQrToken(tokenData.qr_code_token);
            setHistory(historyData);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchData();
    }, [token]);

    React.useEffect(() => {
        if (qrToken) {
            const qrCodeElement = document.getElementById('qrcode');
            if (qrCodeElement) {
                qrCodeElement.innerHTML = ''; // Clear previous QR code
                new QRCode(qrCodeElement, {
                    text: qrToken,
                    width: 256,
                    height: 256,
                });
            }
        }
    }, [qrToken]);

    if (loading) return <p>Cargando control de asistencia...</p>;
    if (error) return <p style={{ color: 'red' }}>{error}</p>;

    return (
        <div>
            <h3>Asistencia y Control de Tiempo (LAN-AT5)</h3>

            <h4>Mi Código QR para Marcar Asistencia</h4>
            <div id="qrcode" style={{ marginBottom: '20px' }}></div>
            <p>Muestra este código en el dispositivo de registro para marcar tu entrada o salida.</p>

            <h4>Mi Historial de Asistencia</h4>
            <table>
                <thead>
                    <tr>
                        <th>Fecha y Hora</th>
                        <th>Evento</th>
                    </tr>
                </thead>
                <tbody>
                    {history.map(record => (
                        <tr key={record.id}>
                            <td>{new Date(record.timestamp).toLocaleString()}</td>
                            <td>{record.event_type}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};
