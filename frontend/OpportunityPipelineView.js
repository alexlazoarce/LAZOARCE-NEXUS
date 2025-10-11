const OpportunityPipelineView = ({ token }) => {
    const [opportunities, setOpportunities] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    const stages = ['Calificación', 'Propuesta', 'Negociación', 'Ganada', 'Perdida'];

    const fetchOpportunities = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/opportunities`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('No se pudieron cargar las oportunidades.');
            const data = await response.json();
            setOpportunities(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchOpportunities();
    }, [token]);

    const handleStageChange = async (oppId, newStage) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/opportunities/${oppId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ stage: newStage })
            });
            if (!response.ok) throw new Error('No se pudo actualizar la oportunidad.');
            fetchOpportunities(); // Refresh the entire pipeline
        } catch (err) {
            setError(err.message);
            alert(`Error: ${err.message}`);
        }
    };

    if (loading) return <p>Cargando pipeline de ventas...</p>;
    if (error) return <p className="error">{error}</p>;

    return (
        <div>
            <h3>Pipeline de Ventas (Oportunidades)</h3>
            <div style={{ display: 'flex', gap: '10px', overflowX: 'auto' }}>
                {stages.map(stage => (
                    <div key={stage} style={{ flex: 1, minWidth: '200px', backgroundColor: '#f4f4f4', padding: '10px', borderRadius: '5px' }}>
                        <h4>{stage}</h4>
                        <div style={{ minHeight: '400px' }}>
                            {opportunities.filter(opp => opp.stage === stage).map(opp => (
                                <div key={opp.id} style={{ border: '1px solid #ccc', backgroundColor: 'white', padding: '8px', marginBottom: '8px', borderRadius: '3px' }}>
                                    <strong>{opp.name}</strong>
                                    <p>Monto: ${opp.amount ? opp.amount.toFixed(2) : 'N/D'}</p>
                                    <div>
                                        <select
                                            value={opp.stage}
                                            onChange={(e) => handleStageChange(opp.id, e.target.value)}
                                        >
                                            {stages.map(s => <option key={s} value={s}>{s}</option>)}
                                        </select>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};