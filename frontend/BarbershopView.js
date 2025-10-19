// frontend/BarbershopView.js

function BarbershopView() {
    const [stylists, setStylists] = React.useState([]);
    const [appointments, setAppointments] = React.useState([]);
    const [selectedDate, setSelectedDate] = React.useState(new Date().toISOString().split('T')[0]);
    const [isLoading, setIsLoading] = React.useState(false);
    const [error, setError] = React.useState('');

    const API_URL = 'http://127.0.0.1:5001/api/barbershop';
    const getAuthToken = () => localStorage.getItem('accessToken');

    const fetchStylists = () => {
        setIsLoading(true);
        fetch(`${API_URL}/stylists`, {
            headers: { 'Authorization': `Bearer ${getAuthToken()}` }
        })
        .then(res => res.json())
        .then(data => {
            setStylists(data);
            setIsLoading(false);
        })
        .catch(err => {
            setError('Error al cargar estilistas.');
            console.error(err);
            setIsLoading(false);
        });
    };

    const fetchAppointments = (date) => {
        setIsLoading(true);
        fetch(`${API_URL}/appointments/${date}`, {
            headers: { 'Authorization': `Bearer ${getAuthToken()}` }
        })
        .then(res => res.json())
        .then(data => {
            setAppointments(data);
            setIsLoading(false);
        })
        .catch(err => {
            setError(`Error al cargar las citas para ${date}.`);
            console.error(err);
            setIsLoading(false);
        });
    };

    React.useEffect(() => {
        fetchStylists();
        fetchAppointments(selectedDate);
    }, [selectedDate]);

    const handleDateChange = (event) => {
        setSelectedDate(event.target.value);
    };

    // Placeholder function for booking an appointment
    const handleBookAppointment = () => alert('Funcionalidad para agendar nueva cita no implementada.');

    return (
        <div style={{ fontFamily: 'Arial, sans-serif', padding: '20px' }}>
            <h1 style={{ color: '#1a365d' }}>Gestión de Barbería (LAN-BAR1)</h1>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <div style={{ display: 'flex', gap: '30px' }}>
                <div style={{ flex: 1 }}>
                    <h2>Estilistas Disponibles</h2>
                    {isLoading && stylists.length === 0 ? <p>Cargando...</p> : (
                        <ul style={{ listStyleType: 'none', padding: 0 }}>
                            {stylists.map(s => (
                                <li key={s.id} style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '5px', borderRadius: '5px' }}>
                                    <strong>{s.name}</strong><br/>
                                    <small>{s.specialty || 'General'}</small>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div style={{ flex: 2 }}>
                    <h2>Agenda de Citas</h2>
                    <div style={{ marginBottom: '15px' }}>
                        <label htmlFor="appointment-date">Seleccionar Fecha: </label>
                        <input
                            type="date"
                            id="appointment-date"
                            value={selectedDate}
                            onChange={handleDateChange}
                            style={{ padding: '8px' }}
                        />
                        <button onClick={handleBookAppointment} style={{ marginLeft: '10px' }}>Agendar Nueva Cita</button>
                    </div>

                    {isLoading && appointments.length === 0 ? <p>Cargando citas...</p> : (
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ backgroundColor: '#f2f2f2' }}>
                                    <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Hora</th>
                                    <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Cliente</th>
                                    <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Estilista</th>
                                    <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {appointments.map(a => (
                                    <tr key={a.id}>
                                        <td style={{ padding: '8px', border: '1px solid #ddd' }}>{new Date(a.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                                        <td style={{ padding: '8px', border: '1px solid #ddd' }}>{a.client}</td>
                                        <td style={{ padding: '8px', border: '1px solid #ddd' }}>{a.stylist}</td>
                                        <td style={{ padding: '8px', border: '1px solid #ddd' }}>{a.status}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}
