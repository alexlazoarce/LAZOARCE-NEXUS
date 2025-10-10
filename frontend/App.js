function App() {
    // Attempt to get the token from localStorage on initial load
    const [token, setToken] = React.useState(localStorage.getItem('jwt_token'));
    // Default view is 'login' if no token, otherwise 'products'
    const [view, setView] = React.useState(token ? 'products' : 'login');
    const [selectedProduct, setSelectedProduct] = React.useState(null);

    // Effect to switch view based on token presence
    React.useEffect(() => {
        if (token) {
            setView('products');
        } else {
            setView('login');
        }
    }, [token]);

    const handleLoginSuccess = (newToken) => {
        localStorage.setItem('jwt_token', newToken);
        setToken(newToken);
    };

    const handleLogout = () => {
        localStorage.removeItem('jwt_token');
        setToken(null);
    };

    const handleSelectProduct = (product) => {
        setSelectedProduct(product);
        setView('apply');
    }

    // This function will be called after a successful application
    const handleApplicationSuccess = () => {
        // Switch view to show the user their applications list
        setView('applications');
    };

    const renderView = () => {
        switch (view) {
            case 'login':
                return <Login onLoginSuccess={handleLoginSuccess} />;
            case 'products':
                return <LoanProducts token={token} onSelectProduct={handleSelectProduct} />;
            case 'apply':
                return <LoanApplicationForm token={token} product={selectedProduct} onApplicationSuccess={handleApplicationSuccess} />;
            case 'applications':
                return <MyApplications token={token} />;
            case 'ledger':
                return <GeneralLedgerView token={token} />;
            default:
                // Fallback to products view if logged in, otherwise login
                return token ? <LoanProducts token={token} onSelectProduct={handleSelectProduct} /> : <Login onLoginSuccess={handleLoginSuccess} />;
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