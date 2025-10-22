const RestaurantView = () => {
    const [menuItems, setMenuItems] = React.useState([]);
    const [tables, setTables] = React.useState([]);
    const [view, setView] = React.useState('tables'); // tables | menu

    const api = useApi();

    const fetchData = async () => {
        try {
            const [menuRes, tablesRes] = await Promise.all([
                api.get('/api/restaurant/menu-items'),
                api.get('/api/restaurant/tables')
            ]);
            setMenuItems(menuRes.data || []);
            setTables(tablesRes.data || []);
        } catch (error) {
            console.error("Error fetching restaurant data:", error);
            alert('Error al cargar datos del restaurante.');
        }
    };

    React.useEffect(() => {
        fetchData();
    }, []);

    const renderTablesView = () => (
        <div className="card">
            <div className="card-header">Mesas</div>
            <div className="card-body">
                <div className="row">
                    {tables.map(table => (
                        <div key={table.id} className="col-md-3 mb-3">
                            <div className={`card text-center ${table.status === 'Ocupada' ? 'border-danger' : 'border-success'}`}>
                                <div className="card-body">
                                    <h5 className="card-title">Mesa {table.table_number}</h5>
                                    <p className="card-text">Capacidad: {table.capacity}</p>
                                    <span className={`badge bg-${table.status === 'Ocupada' ? 'danger' : 'success'}`}>{table.status}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );

    const renderMenuView = () => (
        <div className="card">
            <div className="card-header">Menú</div>
            <div className="card-body">
                <ul className="list-group">
                    {menuItems.map(item => (
                        <li key={item.id} className="list-group-item">
                            <strong>{item.name}</strong> - ${item.price.toFixed(2)}
                            <small className="d-block">{item.description}</small>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );

    return (
        <div className="container-fluid">
            <h1>Gestión de Restaurantes (LAN-RST1)</h1>
            <p>POS, mesas, inventario de ingredientes, y más.</p>

            <ul className="nav nav-tabs">
                <li className="nav-item"><a className={`nav-link ${view === 'tables' ? 'active' : ''}`} href="#" onClick={() => setView('tables')}>Vista de Mesas</a></li>
                <li className="nav-item"><a className={`nav-link ${view === 'menu' ? 'active' : ''}`} href="#" onClick={() => setView('menu')}>Administrar Menú</a></li>
            </ul>

            <div className="mt-3">
                {view === 'tables' ? renderTablesView() : renderMenuView()}
            </div>
        </div>
    );
};
