const OnboardingView = ({ token }) => {
    const [onboardingData, setOnboardingData] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');

    const fetchOnboardingStatus = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/onboarding/my-status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'No se pudo cargar tu proceso de onboarding.');
            }
            const data = await response.json();
            setOnboardingData(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchOnboardingStatus();
    }, [token]);

    const handleCompleteStep = async (stepId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/onboarding/complete-step`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ step_id: stepId })
            });
            if (!response.ok) throw new Error('No se pudo completar el paso.');

            // Refresh the status after completing a step
            fetchOnboardingStatus();
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) return <p>Cargando tu proceso de Onboarding...</p>;
    if (error) return <p style={{ color: 'red' }}>{error}</p>;
    if (!onboardingData) return <p>No tienes un proceso de onboarding asignado.</p>;

    const { status, checklist } = onboardingData;

    return (
        <div>
            <h3>Mi Proceso de Onboarding (LAN-OBD2)</h3>
            <p><strong>Estado General:</strong> {status}</p>

            <h4>Tareas Pendientes</h4>
            <ul>
                {checklist.map(step => (
                    <li key={step.step_id} style={{ textDecoration: step.completed ? 'line-through' : 'none' }}>
                        <strong>{step.name}</strong>: {step.description}
                        {!step.completed && (
                            <button onClick={() => handleCompleteStep(step.step_id)} style={{ marginLeft: '10px' }}>
                                Marcar como Completado
                            </button>
                        )}
                        {step.type === 'Firma' && step.resource_link && (
                            <a href={step.resource_link} target="_blank" rel="noopener noreferrer" style={{ marginLeft: '10px' }}>
                                Firmar Documento
                            </a>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
};
