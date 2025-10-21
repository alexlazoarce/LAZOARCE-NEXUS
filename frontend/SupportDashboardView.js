const SupportDashboardView = ({ token }) => {
    const [tickets, setTickets] = React.useState([]);
    const [employees, setEmployees] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    // State for viewing a single ticket's details
    const [selectedTicket, setSelectedTicket] = React.useState(null);
    const [comments, setComments] = React.useState([]);
    const [newComment, setNewComment] = React.useState('');

    const fetchData = async () => {
        try {
            setLoading(true);
            const [ticketsRes, employeesRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/tickets`, { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/api/employees`, { headers: { 'Authorization': `Bearer ${token}` } })
            ]);
            if (!ticketsRes.ok) throw new Error('No se pudieron cargar los tickets.');
            if (!employeesRes.ok) throw new Error('No se pudieron cargar los empleados.');

            setTickets(await ticketsRes.json());
            setEmployees(await employeesRes.json());
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    };

    React.useEffect(() => { if (!selectedTicket) fetchData(); }, [token, selectedTicket]);

    const handleSelectTicket = async (ticket) => {
        setSelectedTicket(ticket);
        try {
            const response = await fetch(`${API_BASE_URL}/api/tickets/${ticket.id}/comments`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) throw new Error('No se pudieron cargar los comentarios.');
            setComments(await response.json());
        } catch (err) { setError(err.message); }
    };

    // Placeholder for update logic
    const handleUpdateTicket = async (ticketId, updateData) => {
        alert(`Lógica de actualización no implementada. Datos: ${JSON.stringify(updateData)}`);
        // Here you would call the PUT /api/tickets/<id> endpoint
    };

    // Reusing client's comment logic
    const handleAddComment = async (e) => {
        e.preventDefault();
        if (!selectedTicket) return;
        try {
            await fetch(`${API_BASE_URL}/api/tickets/${selectedTicket.id}/comments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ comment_text: newComment })
            });
            setNewComment('');
            handleSelectTicket(selectedTicket);
        } catch (err) { setError(err.message); }
    };

    if (selectedTicket) {
        // Re-use a similar detail view as the client
        return (
             <div>
                <button onClick={() => setSelectedTicket(null)}>← Volver al Dashboard</button>
                <h3>Ticket #{selectedTicket.id}: {selectedTicket.subject}</h3>
                <p><strong>Cliente:</strong> {selectedTicket.created_by}</p>
                {/* Add controls for status, priority, assignment */}
                <div style={{border: '1px solid #eee', padding: '10px', maxHeight: '400px', overflowY: 'auto'}}>
                    {comments.map((c, index) => (
                        <div key={index} style={{borderBottom: '1px solid #ddd', marginBottom: '10px'}}>
                            <p><strong>{c.commenter_name}</strong> ({new Date(c.timestamp).toLocaleString()})</p>
                            <p>{c.comment_text}</p>
                        </div>
                    ))}
                </div>
                <form onSubmit={handleAddComment} style={{marginTop: '10px'}}>
                    <textarea value={newComment} onChange={e => setNewComment(e.target.value)} placeholder="Escribe una respuesta..." required style={{width: '100%', minHeight: '80px'}}></textarea>
                    <button type="submit">Enviar Respuesta</button>
                </form>
            </div>
        );
    }

    if (loading) return <p>Cargando dashboard de soporte...</p>;

    return (
        <div>
            <h3>Dashboard de Soporte</h3>
            {error && <p style={{color:'red'}}>{error}</p>}
            <table>
                <thead><tr><th>ID</th><th>Asunto</th><th>Cliente</th><th>Estado</th><th>Prioridad</th><th>Asignado a</th><th>Acción</th></tr></thead>
                <tbody>
                    {tickets.map(t => (
                        <tr key={t.id}>
                            <td>#{t.id}</td><td>{t.subject}</td><td>{t.created_by}</td><td>{t.status}</td><td>{t.priority}</td><td>{t.assigned_to}</td>
                            <td><button onClick={() => handleSelectTicket(t)}>Ver/Responder</button></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};