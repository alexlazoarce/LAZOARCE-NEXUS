const ClientTicketsView = ({ token }) => {
    const [tickets, setTickets] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    // State for creating a new ticket
    const [newTicket, setNewTicket] = React.useState({ subject: '', description: '' });

    // State for viewing a single ticket's details
    const [selectedTicket, setSelectedTicket] = React.useState(null);
    const [comments, setComments] = React.useState([]);
    const [newComment, setNewComment] = React.useState('');

    const fetchTickets = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/tickets`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) throw new Error('No se pudieron cargar tus tickets.');
            const data = await response.json();
            setTickets(data);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    };

    React.useEffect(() => { if (!selectedTicket) fetchTickets(); }, [token, selectedTicket]);

    const handleCreateTicket = async (e) => {
        e.preventDefault();
        try {
            await fetch(`${API_BASE_URL}/api/tickets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(newTicket)
            });
            setNewTicket({ subject: '', description: '' });
            fetchTickets();
        } catch (err) { setError(err.message); }
    };

    const handleSelectTicket = async (ticket) => {
        setSelectedTicket(ticket);
        try {
            const response = await fetch(`${API_BASE_URL}/api/tickets/${ticket.id}/comments`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) throw new Error('No se pudieron cargar los comentarios.');
            setComments(await response.json());
        } catch (err) { setError(err.message); }
    };

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
            handleSelectTicket(selectedTicket); // Refresh comments
        } catch (err) { setError(err.message); }
    };

    if (selectedTicket) {
        return (
            <div>
                <button onClick={() => setSelectedTicket(null)}>← Volver a Mis Tickets</button>
                <h3>Ticket #{selectedTicket.id}: {selectedTicket.subject}</h3>
                <p><strong>Estado:</strong> {selectedTicket.status} | <strong>Prioridad:</strong> {selectedTicket.priority}</p>
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

    return (
        <div>
            <h3>Mis Tickets de Soporte</h3>
            {error && <p style={{color:'red'}}>{error}</p>}
            <form onSubmit={handleCreateTicket} style={{border: '1px solid #ccc', padding: '10px', marginBottom: '20px'}}>
                <h4>Crear Nuevo Ticket</h4>
                <input value={newTicket.subject} onChange={e => setNewTicket({...newTicket, subject: e.target.value})} placeholder="Asunto" required />
                <textarea value={newTicket.description} onChange={e => setNewTicket({...newTicket, description: e.target.value})} placeholder="Describe tu problema..." required></textarea>
                <button type="submit">Abrir Ticket</button>
            </form>
            <table>
                <thead><tr><th>ID</th><th>Asunto</th><th>Estado</th><th>Última Actualización</th><th>Acción</th></tr></thead>
                <tbody>
                    {tickets.map(t => (
                        <tr key={t.id}>
                            <td>#{t.id}</td><td>{t.subject}</td><td>{t.status}</td><td>{new Date(t.updated_at).toLocaleString()}</td>
                            <td><button onClick={() => handleSelectTicket(t)}>Ver Detalles</button></td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};