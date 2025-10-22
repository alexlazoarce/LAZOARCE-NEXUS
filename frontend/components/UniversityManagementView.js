// frontend/components/UniversityManagementView.js

function UniversityManagementView() {
    return (
        <div>
            <h1>Gestión Universitaria (LAN-UNV8)</h1>
            <p>Este es un placeholder para el módulo de Gestión Universitaria.</p>
            <p>Aquí se gestionarán planes de estudio, becas, biblioteca y egresados.</p>

            <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
                {/* Columna de Planes de Estudio */}
                <div style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '5px' }}>
                    <h2>Planes de Estudio</h2>
                    <ul>
                        <li>Ingeniería en Sistemas</li>
                        <li>Licenciatura en Administración</li>
                        <li>Doctorado en Economía</li>
                    </ul>
                    <button>+ Añadir Programa</button>
                </div>

                {/* Columna de Becas */}
                <div style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '5px' }}>
                    <h2>Becas Disponibles</h2>
                    <ul>
                        <li>Beca al Mérito Académico</li>
                        <li>Beca de Apoyo Financiero</li>
                    </ul>
                    <button>+ Añadir Beca</button>
                </div>
            </div>
        </div>
    );
}
