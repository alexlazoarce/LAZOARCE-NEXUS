function App() {
    const [token, setToken] = React.useState(localStorage.getItem('jwt_token'));
    const [view, setView] = React.useState(token ? 'products' : 'login');
    const [selectedProduct, setSelectedProduct] = React.useState(null);
    const [viewingLoanId, setViewingLoanId] = React.useState(null); // State for loan detail view

    React.useEffect(() => {
        if (!token) {
            setView('login');
        } else if (!viewingLoanId) {
            // Don't change the view if we are looking at details
            // This allows returning to the previous view.
        }
    }, [token]);

    const handleLoginSuccess = (newToken) => {
        localStorage.setItem('jwt_token', newToken);
        setToken(newToken);
        setView('products');
    };

    const handleLogout = () => {
        localStorage.removeItem('jwt_token');
        setToken(null);
        setViewingLoanId(null);
    };

    const handleSelectProduct = (product) => {
        setSelectedProduct(product);
        setView('apply');
    };

    const handleApplicationSuccess = () => {
        setView('applications');
    };

    const handleViewDetails = (loanId) => {
        setViewingLoanId(loanId);
    };

    const handleBackToList = () => {
        setViewingLoanId(null);
        setView('applications');
    }

    // If a loan detail is being viewed, render it exclusively.
    if (token && viewingLoanId) {
        return (
             <div className="container">
                <header>
                    <h1>Sistema de Préstamos Lazo Arce</h1>
                    <button onClick={handleLogout} style={{float: 'right'}}>Cerrar Sesión</button>
                </header>
                <main>
                    <LoanDetailView token={token} loanId={viewingLoanId} onBack={handleBackToList} />
                </main>
            </div>
        );
    }

    const renderView = () => {
        switch (view) {
            case 'login':
                return <Login onLoginSuccess={handleLoginSuccess} />;
            case 'products':
                return <LoanProducts token={token} onSelectProduct={handleSelectProduct} />;
            case 'apply':
                return <LoanApplicationForm token={token} product={selectedProduct} onApplicationSuccess={handleApplicationSuccess} />;
            case 'applications':
                return <MyApplications token={token} onViewDetails={handleViewDetails} />;
            case 'ledger':
                return <GeneralLedgerView token={token} />;
            default:
                return <Login onLoginSuccess={handleLoginSuccess} />;
        }
    };

    return (
        <div className="container">
            <header>
                <h1>Sistema de Préstamos Lazo Arce</h1>
                {token && <button onClick={handleLogout} style={{float: 'right'}}>Cerrar Sesión</button>}
            </header>

            {token && (
                <nav style={{ margin: '1em 0', borderBottom: '1px solid #ddd', paddingBottom: '1em' }}>
                    <button onClick={() => setView('products')}>Ver Productos</button>
                    <button onClick={() => setView('applications')} style={{ marginLeft: '10px' }}>Mis Solicitudes</button>
                    <button onClick={() => setView('ledger')} style={{ marginLeft: '10px' }}>Ver Libro Mayor</button>
                </nav>
            )}

            <main>
                {renderView()}
            </main>
        </div>
    );
}