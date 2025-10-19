const PortfolioView = ({ token }) => {
    const [portfolioData, setPortfolioData] = React.useState({ portfolio: [], summary: {} });
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [filter, setFilter] = React.useState('Todos'); // 'Todos', 'En Mora', 'Al Día'

    React.useEffect(() => {
        const fetchPortfolio = async () => {
            try {
                setLoading(true);
                // Updated endpoint to fetch user-specific portfolio data
                const response = await fetch(`${API_BASE_URL}/api/portfolio/user_status`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) throw new Error('No se pudo cargar la cartera de préstamos.');
                const data = await response.json();
                setPortfolioData(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchPortfolio();
    }, [token]);

    const filteredPortfolio = portfolioData.portfolio.filter(loan => {
        if (filter === 'Todos') return true;
        return loan.status === filter;
    });

    if (loading) return <p>Cargando cartera...</p>;
    if (error) return <p className="error" style={{color: 'red'}}>{error}</p>;

    const { summary } = portfolioData;

    return (
        <div>
            <h3>Resumen de Cartera</h3>
            <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '20px', padding: '10px', backgroundColor: '#f7f7f7' }}>
                <div><strong>Ventas (Desembolsado):</strong> ${summary.total_ventas?.toFixed(2)}</div>
                <div><strong>Recuperado:</strong> ${summary.total_recuperado?.toFixed(2)}</div>
                <div><strong>Saldo Pendiente:</strong> ${summary.total_outstanding?.toFixed(2)}</div>
                <div><strong>Préstamos Activos:</strong> {summary.active_loans}</div>
            </div>

            <h3>Cartera de Préstamos Activos</h3>
            <div>
                <label>Filtrar por estado: </label>
                <select value={filter} onChange={e => setFilter(e.target.value)}>
                    <option value="Todos">Todos</option>
                    <option value="En Mora">En Mora</option>
                    <option value="Al Día">Al Día</option>
                </select>
            </div>
            <table style={{ width: '100%', marginTop: '10px' }}>
                <thead>
                    <tr>
                        <th>ID Préstamo</th>
                        <th>Cliente</th>
                        <th>Saldo Pendiente</th>
                        <th>Estado</th>
                        <th>Días de Mora</th>
                        <th>Próximo Vencimiento</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredPortfolio.map(loan => (
                        <tr key={loan.loan_id} style={{ backgroundColor: loan.status === 'En Mora' ? '#ffdddd' : 'transparent' }}>
                            <td>{loan.loan_id}</td>
                            <td>{loan.customer_name}</td>
                            <td>${loan.outstanding_balance.toFixed(2)}</td>
                            <td>{loan.status}</td>
                            <td>{loan.days_delinquent}</td>
                            <td>{loan.next_due_date}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};