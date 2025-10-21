const HealthView = () => {
    const [patients, setPatients] = React.useState([]);
    const [appointments, setAppointments] = React.useState([]);
    const [selectedPatient, setSelectedPatient] = React.useState(null);
    const [view, setView] = React.useState('appointments'); // appointments | patients

    const [showPatientModal, setShowPatientModal] = React.useState(false);
    const [showAppointmentModal, setShowAppointmentModal] = React.useState(false);

    const api = useApi();

    const fetchData = async () => {
        try {
            const patientsResponse = await api.get('/api/health/patients');
            setPatients(patientsResponse.data || []);
            const appointmentsResponse = await api.get('/api/health/appointments');
            setAppointments(appointmentsResponse.data || []);
        } catch (error) {
            console.error("Error fetching health data:", error);
            alert('Error al cargar los datos de salud.');
        }
    };

    React.useEffect(() => {
        fetchData();
    }, []);

    const handleCreatePatient = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        try {
            await api.post('/api/health/patients', data);
            setShowPatientModal(false);
            fetchData();
            alert('Registro de paciente creado con éxito.');
        } catch (error) {
            console.error("Error creating patient:", error);
            alert('Error al crear el paciente.');
        }
    };

    const handleCreateAppointment = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        try {
            await api.post('/api/health/appointments', data);
            setShowAppointmentModal(false);
            fetchData();
            alert('Cita médica creada con éxito.');
        } catch (error) {
            console.error("Error creating appointment:", error);
            alert('Error al crear la cita.');
        }
    };

    const renderAppointmentsView = () => (
        <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
                Citas Médicas
                <button className="btn btn-sm btn-primary" onClick={() => setShowAppointmentModal(true)}>Programar Cita</button>
            </div>
            <div className="card-body">
                <table className="table table-striped">
                    <thead>
                        <tr>
                            <th>Fecha y Hora</th>
                            <th>Paciente</th>
                            <th>Doctor</th>
                            <th>Motivo</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {appointments.map(app => (
                            <tr key={app.id}>
                                <td>{new Date(app.appointment_time).toLocaleString()}</td>
                                <td>{app.patient_name}</td>
                                <td>{app.doctor_name}</td>
                                <td>{app.reason}</td>
                                <td><span className="badge bg-info">{app.status}</span></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );

    const renderPatientsView = () => (
        <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
                Registros de Pacientes
                <button className="btn btn-sm btn-primary" onClick={() => setShowPatientModal(true)}>Nuevo Paciente</button>
            </div>
            <div className="card-body">
                <ul className="list-group">
                    {patients.map(p => (
                        <li key={p.id} className="list-group-item">
                            <strong>{p.full_name}</strong> (Nacido: {p.birth_date || 'N/A'})
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );

    return (
        <div className="container-fluid">
            <h1>Gestión de Salud (LAN-H7S)</h1>
            <p>Citas médicas, historial clínico, facturación médica, recetas y laboratorios.</p>

            <ul className="nav nav-tabs">
                <li className="nav-item"><a className={`nav-link ${view === 'appointments' ? 'active' : ''}`} href="#" onClick={() => setView('appointments')}>Citas</a></li>
                <li className="nav-item"><a className={`nav-link ${view === 'patients' ? 'active' : ''}`} href="#" onClick={() => setView('patients')}>Pacientes</a></li>
            </ul>

            <div className="mt-3">
                {view === 'appointments' ? renderAppointmentsView() : renderPatientsView()}
            </div>

            {/* Modal para nuevo paciente */}
            {showPatientModal && (
                <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog"><div className="modal-content">
                        <form onSubmit={handleCreatePatient}>
                            <div className="modal-header"><h5 className="modal-title">Nuevo Paciente</h5><button type="button" className="btn-close" onClick={() => setShowPatientModal(false)}></button></div>
                            <div className="modal-body">
                                <div className="mb-3"><label className="form-label">Nombre Completo</label><input type="text" className="form-control" name="full_name" required /></div>
                                <div className="mb-3"><label className="form-label">Fecha de Nacimiento</label><input type="date" className="form-control" name="birth_date" /></div>
                                <div className="mb-3"><label className="form-label">Resumen de Historial Médico</label><textarea className="form-control" name="medical_history_summary"></textarea></div>
                            </div>
                            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowPatientModal(false)}>Cerrar</button><button type="submit" className="btn btn-primary">Guardar</button></div>
                        </form>
                    </div></div>
                </div>
            )}

            {/* Modal para nueva cita */}
            {showAppointmentModal && (
                 <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog"><div className="modal-content">
                        <form onSubmit={handleCreateAppointment}>
                            <div className="modal-header"><h5 className="modal-title">Programar Nueva Cita</h5><button type="button" className="btn-close" onClick={() => setShowAppointmentModal(false)}></button></div>
                            <div className="modal-body">
                                <div className="mb-3">
                                    <label className="form-label">Paciente</label>
                                    <select className="form-select" name="patient_id" required>
                                        <option value="">Seleccione un paciente</option>
                                        {patients.map(p => <option key={p.id} value={p.id}>{p.full_name}</option>)}
                                    </select>
                                </div>
                                 <div className="mb-3"><label className="form-label">ID del Doctor</label><input type="number" className="form-control" name="doctor_id" required /></div>
                                <div className="mb-3"><label className="form-label">Fecha y Hora</label><input type="datetime-local" className="form-control" name="appointment_time" required /></div>
                                <div className="mb-3"><label className="form-label">Motivo de la Consulta</label><textarea className="form-control" name="reason"></textarea></div>
                            </div>
                            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowAppointmentModal(false)}>Cerrar</button><button type="submit" className="btn btn-primary">Programar</button></div>
                        </form>
                    </div></div>
                </div>
            )}
        </div>
    );
};
