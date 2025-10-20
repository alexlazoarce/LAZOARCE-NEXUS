const MailingListView = ({ token }) => {
    const [lists, setLists] = React.useState([]);
    const [users, setUsers] = React.useState([]);
    const [selectedList, setSelectedList] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [newListName, setNewListName] = React.useState('');

    const fetchData = async () => {
        try {
            setLoading(true);
            const [listsRes, usersRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/mailing-lists`, { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/api/users`, { headers: { 'Authorization': `Bearer ${token}` } }) // Assuming a /api/users endpoint exists
            ]);
            if (!listsRes.ok) throw new Error('No se pudieron cargar las listas.');
            if (!usersRes.ok) throw new Error('No se pudieron cargar los usuarios.');

            const listsData = await listsRes.json();
            const usersData = await usersRes.json();

            setLists(listsData);
            setUsers(usersData);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchData();
    }, [token]);

    const handleCreateList = async (e) => {
        e.preventDefault();
        try {
            await fetch(`${API_BASE_URL}/api/mailing-lists`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ name: newListName })
            });
            setNewListName('');
            fetchData();
        } catch (err) { setError(err.message); }
    };

    const handleAddMember = async (userId) => {
        if (!selectedList) return;
        try {
            await fetch(`${API_BASE_URL}/api/mailing-lists/${selectedList.id}/members`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ user_id: userId })
            });
            // In a real app, you'd refresh the members of the selected list
            alert('Miembro añadido. Refresque para ver los cambios.');
        } catch (err) { alert(`Error: ${err.message}`); }
    };

    if (loading) return <p>Cargando...</p>;

    return (
        <div>
            <h3>Gestión de Listas de Correo</h3>
            {error && <p style={{color:'red'}}>{error}</p>}
            <div style={{ display: 'flex', gap: '20px' }}>
                <div style={{ flex: 1 }}>
                    <h4>Listas</h4>
                    <form onSubmit={handleCreateList}>
                        <input value={newListName} onChange={e => setNewListName(e.target.value)} placeholder="Nombre de nueva lista" required />
                        <button type="submit">Crear Lista</button>
                    </form>
                    <ul>
                        {lists.map(list => <li key={list.id}><button className="link-button" onClick={() => setSelectedList(list)}>{list.name} ({list.member_count})</button></li>)}
                    </ul>
                </div>
                <div style={{ flex: 2, borderLeft: '1px solid #ccc', paddingLeft: '20px' }}>
                    <h4>{selectedList ? `Añadir Miembros a "${selectedList.name}"` : 'Seleccione una lista'}</h4>
                    {selectedList && (
                        <table>
                            <thead><tr><th>Nombre Usuario</th><th>Email</th><th>Acción</th></tr></thead>
                            <tbody>
                                {users.map(user => (
                                    <tr key={user.id}>
                                        <td>{user.full_name}</td>
                                        <td>{user.email}</td>
                                        <td><button onClick={() => handleAddMember(user.id)}>Añadir</button></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
};