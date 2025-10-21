const LogisticsView = () => {
    const [vehicles, setVehicles] = React.useState([]);
    const [drivers, setDrivers] = React.useState([]);
    const [routes, setRoutes] = React.useState([]);
    const [view, setView] = React.useState('routes'); // routes | vehicles | drivers

    const api = useApi();

    const fetchData = async () => {
        try {
            const [vehiclesRes, driversRes, routesRes] = await Promise.all([
                api.get('/api/logistics/vehicles'),
                api.get('/api/logistics/drivers'),
                api.get('/api/logistics/routes')
            ]);
            setVehicles(vehiclesRes.data || []);
            setDrivers(driversRes.data || []);
            setRoutes(routesRes.data || []);
        } catch (error) {
            console.error("Error fetching logistics data:", error);
            alert('Error al cargar datos de logística.');
        }
    };

    React.useEffect(() => {
        fetchData();
    }, []);

    const renderRoutesView = () => (
        <div className="card">
            <div className="card-header">Rutas</div>
            <div className="card-body">
                {/* Simplified view */}
                <ul className="list-group">
                    {routes.map(r => <li key={r.id} className="list-group-item">{r.name} - {r.status}</li>)}
                </ul>
            </div>
        </div>
    );

    const renderVehiclesView = () => (
        <div className="card">
            <div className="card-header">Vehículos</div>
            <div className="card-body">
                 <ul className="list-group">
                    {vehicles.map(v => <li key={v.id} className="list-group-item">{v.brand} {v.model} ({v.plate}) - {v.status}</li>)}
                </ul>
            </div>
        </div>
    );

    const renderDriversView = () => (
        <div className="card">
            <div className="card-header">Conductores</div>
            <div className="card-body">
                <ul className="list-group">
                    {drivers.map(d => <li key={d.id} className="list-group-item">{d.user_id} - Licencia: {d.license_number}</li>)}
                </ul>
            </div>
        </div>
    );

    return (
        <div className="container-fluid">
            <h1>Gestión de Logística (LAN-LOG6)</h1>
            <p>Rutas, vehículos, conductores, entregas y mantenimiento.</p>

            <ul className="nav nav-tabs">
                <li className="nav-item"><a className={`nav-link ${view === 'routes' ? 'active' : ''}`} href="#" onClick={() => setView('routes')}>Rutas</a></li>
                <li className="nav-item"><a className={`nav-link ${view === 'vehicles' ? 'active' : ''}`} href="#" onClick={() => setView('vehicles')}>Vehículos</a></li>
                <li className="nav-item"><a className={`nav-link ${view === 'drivers' ? 'active' : ''}`} href="#" onClick={() => setView('drivers')}>Conductores</a></li>
            </ul>

            <div className="mt-3">
                {view === 'routes' && renderRoutesView()}
                {view === 'vehicles' && renderVehiclesView()}
                {view === 'drivers' && renderDriversView()}
            </div>
        </div>
    );
};
