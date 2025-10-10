function EmployeeManagement({ token }) {
    const [employees, setEmployees] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [isEditing, setIsEditing] = React.useState(null); // Holds the employee being edited
    const [isCreating, setIsCreating] = React.useState(false);

    const initialFormState = {
        full_name: '',
        email: '',
        position: '',
        base_salary: '',
        password: '' // Only for new users
    };
    const [formData, setFormData] = React.useState(initialFormState);

    const fetchEmployees = async () => {
        setIsLoading(true);
        setError('');
        try {
            const res = await fetch(`${API_BASE_URL}/api/employees`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Failed to fetch employees');
            setEmployees(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    React.useEffect(() => {
        fetchEmployees();
    }, [token]);

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleEditClick = (employee) => {
        setIsEditing(employee.id);
        setFormData({
            full_name: employee.full_name,
            email: employee.email,
            position: employee.position,
            base_salary: employee.base_salary,
            is_active: employee.is_active
        });
    };

    const handleCancel = () => {
        setIsEditing(null);
        setIsCreating(false);
        setFormData(initialFormState);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const url = isEditing
            ? `${API_BASE_URL}/api/employees/${isEditing}`
            : `${API_BASE_URL}/api/employees`;
        const method = isEditing ? 'PUT' : 'POST';

        try {
            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData)
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Failed to save employee');

            alert(`Empleado ${isEditing ? 'actualizado' : 'creado'} con éxito.`);
            handleCancel();
            fetchEmployees(); // Refresh the list
        } catch (err) {
            setError(err.message);
        }
    };

    const renderForm = () => (
        <div style={{ border: '1px solid #ccc', padding: '1em', margin: '1em 0' }}>
            <h3>{isEditing ? 'Editar Empleado' : 'Crear Nuevo Empleado'}</h3>
            <form onSubmit={handleSubmit}>
                <input name="full_name" value={formData.full_name} onChange={handleInputChange} placeholder="Nombre Completo" required />
                <input name="email" type="email" value={formData.email} onChange={handleInputChange} placeholder="Email" required />
                {!isEditing && <input name="password" type="password" value={formData.password} onChange={handleInputChange} placeholder="Contraseña Inicial" required />}
                <input name="position" value={formData.position} onChange={handleInputChange} placeholder="Cargo" required />
                <input name="base_salary" type="number" step="0.01" value={formData.base_salary} onChange={handleInputChange} placeholder="Salario Base" required />
                {isEditing && <label><input type="checkbox" name="is_active" checked={formData.is_active} onChange={e => setFormData({...formData, is_active: e.target.checked})} /> Activo</label>}
                <button type="submit">Guardar</button>
                <button type="button" onClick={handleCancel}>Cancelar</button>
            </form>
        </div>
    );

    return (
        <div>
            <h2>Gestión de Empleados</h2>
            {error && <p style={{color: 'red'}}>{error}</p>}

            {!isEditing && !isCreating && <button onClick={() => setIsCreating(true)}>Añadir Empleado</button>}
            {(isEditing || isCreating) && renderForm()}

            {isLoading ? <p>Cargando...</p> : (
                <table>
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Email</th>
                            <th>Cargo</th>
                            <th>Salario Base</th>
                            <th>Estado</th>
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
                                <td>{emp.is_active ? 'Activo' : 'Inactivo'}</td>
                                <td><button onClick={() => handleEditClick(emp)}>Editar</button></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}