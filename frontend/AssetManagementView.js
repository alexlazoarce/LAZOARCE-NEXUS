// frontend/AssetManagementView.js

const AssetManagementView = () => {
    const [assets, setAssets] = React.useState([]);
    const [selectedAsset, setSelectedAsset] = React.useState(null);

    const mockAssets = [
        { id: 1, name: 'Laptop Gerencia', purchase_cost: 1500, status: 'Activo', book_value: 1250 },
        { id: 2, name: 'Servidor Principal', purchase_cost: 5000, status: 'Activo', book_value: 4500 },
        { id: 3, name: 'Escritorio Oficina 1', purchase_cost: 300, status: 'Dado de Baja', book_value: 0 },
    ];

    const mockDepreciation = {
        1: [
            { id: 101, entry_date: '2023-10-01', amount: 50 },
            { id: 102, entry_date: '2023-11-01', amount: 50 },
        ],
        2: [
            { id: 201, entry_date: '2023-11-01', amount: 100 },
        ],
        3: []
    };

    React.useEffect(() => {
        setAssets(mockAssets);
    }, []);

    const handleSelectAsset = (asset) => {
        setSelectedAsset(asset);
    };

    if (selectedAsset) {
        return (
            <div className="container">
                <button className="btn btn-secondary mb-3" onClick={() => setSelectedAsset(null)}>
                    &larr; Volver a Activos
                </button>
                <h3>{selectedAsset.name}</h3>
                <p><strong>Costo de Compra:</strong> ${selectedAsset.purchase_cost.toFixed(2)}</p>
                <p><strong>Valor en Libros:</strong> ${selectedAsset.book_value.toFixed(2)}</p>

                <div className="card">
                    <div className="card-header d-flex justify-content-between">
                        <span>Historial de Depreciación</span>
                        <button className="btn btn-primary btn-sm">Calcular Depreciación del Mes</button>
                    </div>
                    <div className="card-body">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Fecha</th>
                                    <th>Monto Depreciado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {(mockDepreciation[selectedAsset.id] || []).map(entry => (
                                    <tr key={entry.id}>
                                        <td>{new Date(entry.entry_date).toLocaleDateString()}</td>
                                        <td>${entry.amount.toFixed(2)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="container">
            <h2>LAN-AFX4: Gestión de Activos Fijos</h2>
            <div className="card">
                <div className="card-header d-flex justify-content-between">
                    <span>Lista de Activos</span>
                    <button className="btn btn-primary btn-sm">Añadir Nuevo Activo</button>
                </div>
                <div className="card-body">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Nombre del Activo</th>
                                <th>Costo de Compra</th>
                                <th>Valor en Libros</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {assets.map(asset => (
                                <tr key={asset.id}>
                                    <td>{asset.name}</td>
                                    <td>${asset.purchase_cost.toFixed(2)}</td>
                                    <td>${asset.book_value.toFixed(2)}</td>
                                    <td>{asset.status}</td>
                                    <td>
                                        <button className="btn btn-sm btn-info" onClick={() => handleSelectAsset(asset)}>
                                            Ver Detalles
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
