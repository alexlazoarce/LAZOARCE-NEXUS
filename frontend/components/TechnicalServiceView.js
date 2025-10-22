const TechnicalServiceView = () => {
    const [jobs, setJobs] = React.useState([]);

    const api = useApi();

    const fetchJobs = async () => {
        try {
            const response = await api.get('/api/technical-services/jobs');
            setJobs(response.data || []);
        } catch (error) {
            console.error("Error fetching service jobs:", error);
            alert('Error al cargar los trabajos de servicio.');
        }
    };

    React.useEffect(() => {
        fetchJobs();
    }, []);

    return (
        <div className="container-fluid">
            <h1>Gestión de Servicios Técnicos (LAN-JO1B)</h1>
            <p>Cotizaciones móviles, programación de citas, facturación en sitio y seguimiento de rentabilidad por trabajo.</p>

            <div className="card">
                <div className="card-header">
                    Trabajos de Servicio
                </div>
                <div className="card-body">
                    <table className="table table-striped">
                        <thead>
                            <tr>
                                <th>Título</th>
                                <th>Cliente</th>
                                <th>Asignado a</th>
                                <th>Fecha Programada</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {jobs.map(job => (
                                <tr key={job.id}>
                                    <td>{job.title}</td>
                                    <td>{job.contact_id}</td>
                                    <td>{job.assigned_to_id}</td>
                                    <td>{job.scheduled_date ? new Date(job.scheduled_date).toLocaleDateString() : 'N/A'}</td>
                                    <td><span className="badge bg-primary">{job.status}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
