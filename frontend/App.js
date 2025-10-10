function App() {
    const [token, setToken] = React.useState(localStorage.getItem('jwt_token'));
    const [user, setUser] = React.useState(null);
    const [view, setView] = React.useState('login');
    const [selectedProduct, setSelectedProduct] = React.useState(null);
    const [viewingLoanId, setViewingLoanId] = React.useState(null);
    const [viewingContractId, setViewingContractId] = React.useState(null);

    React.useEffect(() => {
        const currentToken = localStorage.getItem('jwt_token');
        if (currentToken) {
            setToken(currentToken);
            try {
                const payload = JSON.parse(atob(currentToken.split('.')[1]));
                setUser({ email: payload.sub, role: payload.role });
                if (!viewingLoanId && !viewingContractId) {
                    setView('products');
                }
            } catch (e) {
                console.error("Invalid token:", e);
                handleLogout();
            }
        } else {
            setView('login');
            setUser(null);
        }
    }, []);

    const handleLoginSuccess = (newToken) => {
        localStorage.setItem('jwt_token', newToken);
        setToken(newToken);
        const payload = JSON.parse(atob(newToken.split('.')[1]));
        setUser({ email: payload.sub, role: payload.role });
        setView('products');
    };

    const handleLogout = () => {
        localStorage.removeItem('jwt_token');
        setToken(null);
        setUser(null);
        setViewingLoanId(null);
        setViewingContractId(null);
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
    };

    const handleViewContract = (loanId) => {
        setViewingContractId(loanId);
    };

    const handleBackFromContract = () => {
        setViewingContractId(null);
        setView('applications');
    };

    if (token && viewingLoanId) {
        return (
            <div className="container">
                <header><h1>Sistema de Préstamos Lazo Arce</h1><button onClick={handleLogout} style={{float: 'right'}}>Cerrar Sesión</button></header>
                <main><LoanDetailView token={token} loanId={viewingLoanId} onBack={handleBackToList} /></main>
            </div>
        );
    }

    if (token && viewingContractId) {
        return (
            <div className="container">
                <header><h1>Sistema de Préstamos Lazo Arce</h1><button onClick={handleLogout} style={{float: 'right'}}>Cerrar Sesión</button></header>
                <main><ContractView token={token} loanId={viewingContractId} onBack={handleBackFromContract} /></main>
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
                return <MyApplications token={token} onViewDetails={handleViewDetails} onViewContract={handleViewContract} />;
            case 'ledger':
                return <GeneralLedgerView token={token} />;
            case 'profile':
                return <Profile token={token} />;
            case 'rrhh':
                return (
                    <div>
                        <EmployeeManagement token={token} />
                        <PayrollView token={token} />
                    </div>
                );
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
                    <button onClick={() => setView('profile')} style={{ marginLeft: '10px' }}>Mi Perfil</button>
                    {user && user.role === 'Admin' && (
                        <button onClick={() => setView('rrhh')} style={{ marginLeft: '10px' }}>RRHH</button>
                    )}
                </nav>
            )}

            <main>
                {renderView()}
            </main>
        </div>
    );
}