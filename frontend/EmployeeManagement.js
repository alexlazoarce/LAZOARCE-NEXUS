const EmployeeManagement = ({ token }) => {
    const [employees, setEmployees] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    // Form state for adding/editing an employee
    const [form, setForm] = React.useState({
        id: null,
        full_name: '',
        position: '',
        salary: '',
        hire_date: '',
        dui: '',
        nit: '',
        isss_number: '',
        afp_number: '',
    });
    const [isEditing, setIsEditing] = React.useState(false);

    const fetchEmployees = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/employees`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudieron cargar los empleados.');
            const data = await response.json();
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

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setForm(prev => ({ ...prev, [name]: value }));
    };

    const resetForm = () => {
        setForm({ id: null, full_name: '', position: '', salary: '', hire_date: '', dui: '', nit: '', isss_number: '', afp_number: '' });
        setIsEditing(false);
    };

    const handleEditClick = (employee) => {
        setForm({ ...employee, hire_date: employee.hire_date.split('T')[0] });
        setIsEditing(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const url = isEditing ? `${API_BASE_URL}/api/employees/${form.id}` : `${API_BASE_URL}/api/employees`;
        const method = isEditing ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(form),
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.message || 'Error al guardar el empleado.');
            }
            resetForm();
            fetchEmployees(); // Refresh list
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) return <p>Cargando empleados...</p>;
    if (error) return <p className="error">{error}</p>;

    return (
        <div>
            <h3>Gestión de Empleados</h3>

            {/* Form for Adding/Editing Employees */}
            <form onSubmit={handleSubmit} style={{ marginBottom: '20px', border: '1px solid #ccc', padding: '10px' }}>
                <h4>{isEditing ? 'Editar Empleado' : 'Agregar Nuevo Empleado'}</h4>
                <input name="full_name" value={form.full_name} onChange={handleInputChange} placeholder="Nombre Completo" required />
                <input name="position" value={form.position} onChange={handleInputChange} placeholder="Cargo" required />
                <input type="number" name="salary" value={form.salary} onChange={handleInputChange} placeholder="Salario Mensual" required />
                <input type="date" name="hire_date" value={form.hire_date} onChange={handleInputChange} required />
                <input name="dui" value={form.dui} onChange={handleInputChange} placeholder="DUI" />
                <button type="submit">{isEditing ? 'Actualizar' : 'Agregar'}</button>
                {isEditing && <button type="button" onClick={resetForm}>Cancelar Edición</button>}
            </form>

            {/* List of Employees */}
            <table>
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Cargo</th>
                        <th>Salario</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {employees.map(emp => (
                        <tr key={emp.id}>
                            <td>{emp.full_name}</td>
                            <td>{emp.position}</td>
                            <td>${emp.salary.toFixed(2)}</td>
                            <td>{emp.is_active ? 'Activo' : 'Inactivo'}</td>
                            <td>
                                <button onClick={() => handleEditClick(emp)}>Editar</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};