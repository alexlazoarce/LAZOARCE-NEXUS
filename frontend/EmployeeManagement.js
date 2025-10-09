const API_BASE_URL = 'http://127.0.0.1:5000';

function EmployeeManagement({ token }) {
    const [employees, setEmployees] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [newEmployee, setNewEmployee] = React.useState({
        full_name: '',
        email: '',
        password: '',
        position: '',
        base_salary: '',
        role: 'Ejecutivo de Crédito' // Rol por defecto para nuevos empleados
    });

    const fetchEmployees = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/employees`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'No se pudieron cargar los empleados.');
            setEmployees(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchEmployees();
    }, [token]);

    const handleNewEmployeeChange = (e) => {
        setNewEmployee({ ...newEmployee, [e.target.name]: e.target.value });
    };

    const handleAddEmployee = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const res = await fetch(`${API_BASE_URL}/api/employees`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(newEmployee)
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg);
            alert('Empleado añadido exitosamente.');
            fetchEmployees(); // Recargar la lista
            setNewEmployee({ full_name: '', email: '', password: '', position: '', base_salary: '', role: 'Ejecutivo de Crédito' });
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) return <p>Cargando empleados...</p>;
    if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

    return (
        <div className="employee-management-container">
            <h3>Gestión de Empleados</h3>
            <div className="form-section">
                <h4>Añadir Nuevo Empleado</h4>
                <form onSubmit={handleAddEmployee}>
                    <input name="full_name" value={newEmployee.full_name} onChange={handleNewEmployeeChange} placeholder="Nombre Completo" required />
                    <input name="email" type="email" value={newEmployee.email} onChange={handleNewEmployeeChange} placeholder="Email" required />
                    <input name="password" type="password" value={newEmployee.password} onChange={handleNewEmployeeChange} placeholder="Contraseña" required />
                    <input name="position" value={newEmployee.position} onChange={handleNewEmployeeChange} placeholder="Cargo" required />
                    <input name="base_salary" type="number" value={newEmployee.base_salary} onChange={handleNewEmployeeChange} placeholder="Salario Base" required />
                    <button type="submit">Añadir Empleado</button>
                </form>
            </div>
            <div className="results-section">
                <h4>Empleados Activos</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Email</th>
                            <th>Cargo</th>
                            <th>Salario Base</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {employees.map(emp => (
                            <tr key={emp.id}>
                                <td>{emp.full_name}</td>
                                <td>{emp.email}</td>
                                <td>{emp.position}</td>
                                <td>${emp.base_salary.toFixed(2)}</td>
                                <td>{/* Botones de Editar/Desactivar irían aquí */}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}