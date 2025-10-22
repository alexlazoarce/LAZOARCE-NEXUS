// frontend/components/CADView.js

function CADView() {
    return (
        <div>
            <h1>Creación de Planos (LAN-CAD)</h1>
            <p>Este es un placeholder para el módulo de gestión de proyectos de diseño CAD.</p>

            <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
                {/* Columna de Proyectos */}
                <div style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '5px', width: '300px' }}>
                    <h2>Proyectos de Diseño</h2>
                    <ul>
                        <li>Proyecto Residencial "Vista Hermosa"</li>
                        <li>Diseño de Puente "El Litoral"</li>
                        <li>Planos de Centro Comercial "Metrópolis"</li>
                    </ul>
                    <button>+ Nuevo Proyecto</button>
                </div>

                {/* Columna de Archivos del Proyecto Seleccionado */}
                <div style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '5px', flex: 1 }}>
                    <h2>Archivos de "Vista Hermosa"</h2>
                    <ul>
                        <li>plano_arquitectonico.dwg (v3)</li>
                        <li>estructural_cimentacion.dxf (v2)</li>
                        <li>modelo_completo.ifc (v1)</li>
                    </ul>
                    <button>+ Cargar Archivo</button>
                </div>
            </div>
        </div>
    );
}
