// frontend/components/SchoolManagementView.js

function SchoolManagementView() {
    return (
        <div>
            <h1>Gestión Escolar (LAN-SCH6)</h1>
            <p>Este es un placeholder para el módulo de Gestión Escolar.</p>
            <p>Aquí se gestionarán estudiantes, cursos, matrículas, calificaciones y pagos.</p>

            <div style={{ display: 'flex', gap: '20px' }}>
                {/* Columna de Estudiantes */}
                <div style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '5px' }}>
                    <h2>Estudiantes</h2>
                    <ul>
                        <li>Juan Pérez - Código: S001</li>
                        <li>Ana Gómez - Código: S002</li>
                    </ul>
                    <button>+ Añadir Estudiante</button>
                </div>

                {/* Columna de Cursos */}
                <div style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '5px' }}>
                    <h2>Cursos</h2>
                    <ul>
                        <li>Matemáticas I - Prof. Carlos Ruiz</li>
                        <li>Historia Universal - Profa. Laura Méndez</li>
                    </ul>
                    <button>+ Añadir Curso</button>
                </div>
            </div>
        </div>
    );
}
