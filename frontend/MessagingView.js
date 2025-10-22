// frontend/MessagingView.js

const MessagingView = () => {
    const [channels, setChannels] = React.useState([]);
    const [messages, setMessages] = React.useState([]);
    const [activeChannel, setActiveChannel] = React.useState(null);
    const [newMessage, setNewMessage] = React.useState('');
    const [loading, setLoading] = React.useState(true);

    const mockChannels = [
        { id: 1, name: 'General', description: 'Canal para anuncios de toda la empresa' },
        { id: 2, name: 'Ventas', description: 'Discusiones del equipo de ventas' },
        { id: 3, name: 'Proyecto Nexus', description: 'Canal privado para el proyecto' }
    ];

    const mockMessages = {
        1: [
            { id: 101, author: 'Admin', content: 'Bienvenidos al canal general.', created_at: '2023-10-26T10:00:00Z' },
            { id: 102, author: 'Jules', content: 'Hola a todos.', created_at: '2023-10-26T10:05:00Z' }
        ],
        2: [
            { id: 201, author: 'Ejecutivo de Ventas', content: 'Nuevo lead de Acme Corp.', created_at: '2023-10-26T11:00:00Z' }
        ],
        3: []
    };

    React.useEffect(() => {
        // Simulación de carga de canales
        setChannels(mockChannels);
        setActiveChannel(mockChannels[0]);
        setLoading(false);
    }, []);

    React.useEffect(() => {
        if (activeChannel) {
            // Simulación de carga de mensajes para el canal activo
            setMessages(mockMessages[activeChannel.id] || []);
        }
    }, [activeChannel]);

    const handleSendMessage = () => {
        if (newMessage.trim() === '') return;

        console.log(`Enviando mensaje "${newMessage}" al canal ${activeChannel.name}`);

        // En una implementación real, esto enviaría el mensaje al backend
        // y actualizaría el estado con la respuesta.
        const sentMessage = {
            id: Date.now(),
            author: 'Yo',
            content: newMessage,
            created_at: new Date().toISOString()
        };
        setMessages([...messages, sentMessage]);
        setNewMessage('');
    };

    if (loading) {
        return <div>Cargando mensajería...</div>;
    }

    return (
        <div className="container" style={{ display: 'flex', height: '80vh' }}>
            {/* Columna de Canales */}
            <div className="card" style={{ width: '30%', marginRight: '1rem' }}>
                <div className="card-header">Canales</div>
                <ul className="list-group list-group-flush">
                    {channels.map(channel => (
                        <li
                            key={channel.id}
                            className={`list-group-item ${activeChannel?.id === channel.id ? 'active' : ''}`}
                            onClick={() => setActiveChannel(channel)}
                            style={{ cursor: 'pointer' }}
                        >
                            {channel.name}
                        </li>
                    ))}
                </ul>
            </div>

            {/* Columna de Chat */}
            <div className="card" style={{ width: '70%', display: 'flex', flexDirection: 'column' }}>
                <div className="card-header">
                    {activeChannel ? activeChannel.name : 'Seleccione un canal'}
                </div>
                <div className="card-body" style={{ flex: 1, overflowY: 'auto' }}>
                    {messages.map(msg => (
                        <div key={msg.id} className="mb-2">
                            <strong>{msg.author}</strong> <small className="text-muted">{new Date(msg.created_at).toLocaleTimeString()}</small>
                            <p>{msg.content}</p>
                        </div>
                    ))}
                </div>
                <div className="card-footer d-flex">
                    <input
                        type="text"
                        className="form-control me-2"
                        placeholder="Escribe un mensaje..."
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    />
                    <button className="btn btn-primary" onClick={handleSendMessage}>Enviar</button>
                </div>
            </div>
        </div>
    );
};
