// frontend/components/LaundryView.js

function LaundryView() {
    return (
        <div>
            <h1>Gestión de Lavandería (LAN-LDR3)</h1>
            <p>Este es un placeholder para el módulo de Gestión de Lavandería.</p>

            <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
                {/* Columna de Órdenes Activas */}
                <div style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '5px', width: '400px' }}>
                    <h2>Órdenes Activas</h2>
                    <ul>
                        <li>Orden #101 - Cliente: Ana Torres - Estado: En Proceso</li>
                        <li>Orden #102 - Cliente: Luis Méndez - Estado: Recibido</li>
                        <li>Orden #103 - Cliente: Sofía Castro - Estado: Listo para Entrega</li>
                    </ul>
                    <button>+ Nueva Orden</button>
                </div>

                {/* Columna de Insumos */}
                <div style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '5px', flex: 1 }}>
                    <h2>Inventario de Insumos</h2>
                    <ul>
                        <li>Detergente Industrial: 50.5 / 100 litros</li>
                        <li>Suavizante Floral: 25.0 / 50 litros</li>
                        <li>Bolsas de Empaque: 850 / 1000 unidades</li>
                    </ul>
                    <button>+ Registrar Compra de Insumo</button>
                </div>
            </div>
        </div>
    );
}
