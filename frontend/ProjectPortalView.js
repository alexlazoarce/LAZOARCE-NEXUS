const ProjectPortalView = ({ token }) => {
    const [projects, setProjects] = React.useState([]);
    const [employees, setEmployees] = React.useState([]);
    const [selectedProject, setSelectedProject] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    const [newProjectName, setNewProjectName] = React.useState('');
    const [newTask, setNewTask] = React.useState({ title: '', assignee_id: '' });

    const taskStages = ['Pendiente', 'En Progreso', 'Hecho'];

    const fetchData = async () => {
        try {
            setLoading(true);
            const [projRes, empRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/projects`, { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/api/employees`, { headers: { 'Authorization': `Bearer ${token}` } })
            ]);
            if (!projRes.ok || !empRes.ok) throw new Error('No se pudieron cargar los datos de proyectos.');

            setProjects(await projRes.json());
            setEmployees(await empRes.json());
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    };

    React.useEffect(() => { fetchData(); }, [token]);

    const handleSelectProject = async (project) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/projects/${project.id}`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) throw new Error('No se pudieron cargar las tareas del proyecto.');
            const data = await response.json();
            setSelectedProject(data);
        } catch (err) { setError(err.message); }
    };

    const handleCreateProject = async (e) => {
        e.preventDefault();
        try {
            await fetch(`${API_BASE_URL}/api/projects`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ name: newProjectName })
            });
            setNewProjectName('');
            fetchData();
        } catch (err) { setError(err.message); }
    };

    const handleCreateTask = async (e) => {
        e.preventDefault();
        if(!selectedProject) return;
        try {
            await fetch(`${API_BASE_URL}/api/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ ...newTask, project_id: selectedProject.id })
            });
            setNewTask({ title: '', assignee_id: '' });
            handleSelectProject(selectedProject); // Refresh tasks
        } catch (err) { setError(err.message); }
    };

    const handleTaskStageChange = async (taskId, newStatus) => {
        try {
            await fetch(`${API_BASE_URL}/api/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ status: newStatus })
            });
            handleSelectProject(selectedProject); // Refresh tasks
        } catch (err) { setError(err.message); }
    };

    if (loading) return <p>Cargando portal de proyectos...</p>;

    return (
        <div>
            <h3>Portal de Proyectos</h3>
            {error && <p style={{color: 'red'}}>{error}</p>}
            <div style={{display: 'flex', gap: '20px'}}>
                <div style={{flex: 1}}>
                    <h4>Proyectos</h4>
                    <form onSubmit={handleCreateProject}><input value={newProjectName} onChange={e => setNewProjectName(e.target.value)} placeholder="Nuevo Proyecto" required /><button type="submit">+</button></form>
                    <ul>{projects.map(p => <li key={p.id}><button className="link-button" onClick={() => handleSelectProject(p)}>{p.name}</button></li>)}</ul>
                </div>
                <div style={{flex: 3, borderLeft: '1px solid #ccc', paddingLeft: '20px'}}>
                    {selectedProject ? (
                        <div>
                            <h4>{selectedProject.name}</h4>
                            <form onSubmit={handleCreateTask}>
                                <input value={newTask.title} onChange={e => setNewTask({...newTask, title: e.target.value})} placeholder="Nueva Tarea" required />
                                <select value={newTask.assignee_id} onChange={e => setNewTask({...newTask, assignee_id: e.target.value})}>
                                    <option value="">Asignar a...</option>
                                    {employees.map(e => <option key={e.id} value={e.id}>{e.full_name}</option>)}
                                </select>
                                <button type="submit">Añadir Tarea</button>
                            </form>
                            <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                                {taskStages.map(stage => (
                                    <div key={stage} style={{ flex: 1, backgroundColor: '#f4f4f4', padding: '10px' }}>
                                        <h5>{stage}</h5>
                                        {selectedProject.tasks.filter(t => t.status === stage).map(t => (
                                            <div key={t.id} style={{border: '1px solid #ddd', padding: '5px', margin: '5px', backgroundColor: 'white'}}>
                                                <p>{t.title}</p>
                                                <small>Asignado a: {t.assignee_name}</small>
                                                <select value={t.status} onChange={(e) => handleTaskStageChange(t.id, e.target.value)}>
                                                    {taskStages.map(s => <option key={s} value={s}>{s}</option>)}
                                                </select>
                                            </div>
                                        ))}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : <p>Seleccione un proyecto para ver sus tareas.</p>}
                </div>
            </div>
        </div>
    );
};