// frontend/GymManagementView.js

function GymManagementView() {
    const [view, setView] = React.useState('members'); // members, plans, classes
    const [members, setMembers] = React.useState([]);
    const [plans, setPlans] = React.useState([]);
    const [classes, setClasses] = React.useState([]);
    const [isLoading, setIsLoading] = React.useState(false);
    const [error, setError] = React.useState('');

    const API_URL = 'http://127.0.0.1:5001/api/gym';
    const getAuthToken = () => localStorage.getItem('accessToken');

    const fetchData = (dataType) => {
        setIsLoading(true);
        fetch(`${API_URL}/${dataType}`, {
            headers: { 'Authorization': `Bearer ${getAuthToken()}` }
        })
        .then(res => res.json())
        .then(data => {
            if (dataType === 'members') setMembers(data);
            if (dataType === 'plans') setPlans(data);
            if (dataType === 'classes') setClasses(data);
            setIsLoading(false);
        })
        .catch(err => {
            setError(`Error al cargar ${dataType}.`);
            console.error(err);
            setIsLoading(false);
        });
    };

    React.useEffect(() => {
        fetchData(view);
    }, [view]);

    // Placeholder functions for creating new items
    const handleAddMember = () => alert('Funcionalidad para añadir miembro no implementada.');
    const handleAddPlan = () => alert('Funcionalidad para añadir plan no implementada.');
    const handleAddClass = () => alert('Funcionalidad para añadir clase no implementada.');

    const renderNav = () => (
        <nav style={{ marginBottom: '20px', borderBottom: '1px solid #ccc', paddingBottom: '10px' }}>
            <button onClick={() => setView('members')} style={view === 'members' ? {fontWeight: 'bold'} : {}}>Miembros</button>
            <button onClick={() => setView('plans')} style={view === 'plans' ? {fontWeight: 'bold', marginLeft: '10px'} : {marginLeft: '10px'}}>Planes</button>
            <button onClick={() => setView('classes')} style={view === 'classes' ? {fontWeight: 'bold', marginLeft: '10px'} : {marginLeft: '10px'}}>Clases</button>
        </nav>
    );

    const renderMembers = () => (
        <div>
            <h2>Miembros ({members.length})</h2>
            <button onClick={handleAddMember}>Añadir Miembro</button>
            <table style={{ width: '100%', marginTop: '10px' }}>
                <thead><tr><th>Nombre</th><th>Email</th><th>Estado</th><th>Vencimiento Membresía</th></tr></thead>
                <tbody>
                    {members.map(m => <tr key={m.id}><td>{m.full_name}</td><td>{m.email}</td><td>{m.status}</td><td>{m.membership_end_date}</td></tr>)}
                </tbody>
            </table>
        </div>
    );

    const renderPlans = () => (
        <div>
            <h2>Planes de Membresía ({plans.length})</h2>
            <button onClick={handleAddPlan}>Añadir Plan</button>
            <table style={{ width: '100%', marginTop: '10px' }}>
                <thead><tr><th>Nombre</th><th>Precio</th><th>Duración (Días)</th></tr></thead>
                <tbody>
                    {plans.map(p => <tr key={p.id}><td>{p.name}</td><td>${p.price}</td><td>{p.duration_days}</td></tr>)}
                </tbody>
            </table>
        </div>
    );

    const renderClasses = () => (
        <div>
            <h2>Clases ({classes.length})</h2>
            <button onClick={handleAddClass}>Añadir Clase</button>
            <table style={{ width: '100%', marginTop: '10px' }}>
                <thead><tr><th>Nombre</th><th>Instructor</th><th>Horario</th></tr></thead>
                <tbody>
                    {classes.map(c => <tr key={c.id}><td>{c.name}</td><td>{c.instructor}</td><td>{c.schedule}</td></tr>)}
                </tbody>
            </table>
        </div>
    );

    return (
        <div style={{ fontFamily: 'Arial, sans-serif', padding: '20px' }}>
            <h1 style={{ color: '#1a365d' }}>Gestión de Gimnasio (LAN-GYM1)</h1>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {renderNav()}
            {isLoading ? <p>Cargando...</p> : (
                <>
                    {view === 'members' && renderMembers()}
                    {view === 'plans' && renderPlans()}
                    {view === 'classes' && renderClasses()}
                </>
            )}
        </div>
    );
}
