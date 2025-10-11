function EmployeeManagement({ token }) {
    const [employees, setEmployees] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [isEditing, setIsEditing] = React.useState(null);
    const [isCreating, setIsCreating] = React.useState(false);
    const initialForm = { full_name: '', email: '', position: '', base_salary: '', password: '' };
    const [formData, setFormData] = React.useState(initialForm);

    const fetchEmployees = () => {
        setIsLoading(true);
        fetch(`${API_BASE_URL}/api/employees`, { headers: { 'Authorization': `Bearer ${token}` } })
            .then(res => res.ok ? res.json() : Promise.reject(res.json()))
            .then(setEmployees)
            .catch(err => err.then(e => setError(e.msg)))
            .finally(() => setIsLoading(false));
    };

    React.useEffect(fetchEmployees, [token]);

    const handleInputChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });
    const handleCancel = () => { setIsEditing(null); setIsCreating(false); setFormData(initialForm); };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const url = isEditing ? `${API_BASE_URL}/api/employees/${isEditing}` : `${API_BASE_URL}/api/employees`;
        const method = isEditing ? 'PUT' : 'POST';
        try {
            const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify(formData) });
            const data = await res.json();
            if (!res.ok) throw new Error(data.msg || 'Error al guardar');
            alert(`Empleado ${isEditing ? 'actualizado' : 'creado'}`);
            handleCancel();
            fetchEmployees();
        } catch (err) {
            setError(err.message);
        }
    };

    const renderForm = () => (
        <div>
            <h3>{isEditing ? 'Editar' : 'Crear'} Empleado</h3>
            <form onSubmit={handleSubmit}>
                <input name="full_name" value={formData.full_name} onChange={handleInputChange} placeholder="Nombre Completo" required />
                <input name="email" type="email" value={formData.email} onChange={handleInputChange} placeholder="Email" required />
                {!isEditing && <input name="password" type="password" value={formData.password} onChange={handleInputChange} placeholder="Contraseña" required />}
                <input name="position" value={formData.position} onChange={handleInputChange} placeholder="Cargo" required />
                <input name="base_salary" type="number" value={formData.base_salary} onChange={handleInputChange} placeholder="Salario Base" required />
                <button type="submit">Guardar</button>
                <button type="button" onClick={handleCancel}>Cancelar</button>
            </form>
        </div>
    );

    return (
        <div>
            <h2>Gestión de Empleados</h2>
            {!isEditing && !isCreating && <button onClick={() => setIsCreating(true)}>Añadir Empleado</button>}
            {(isEditing || isCreating) && renderForm()}
            {isLoading ? <p>Cargando...</p> : (
                <table>
                    <thead><tr><th>Nombre</th><th>Email</th><th>Cargo</th><th>Salario</th><th>Acciones</th></tr></thead>
                    <tbody>{employees.map(emp => <tr key={emp.id}><td>{emp.full_name}</td><td>{emp.email}</td><td>{emp.position}</td><td>${emp.base_salary.toFixed(2)}</td><td><button onClick={() => { setIsEditing(emp.id); setFormData(emp); }}>Editar</button></td></tr>)}</tbody>
                </table>
            )}
        </div>
    );
}