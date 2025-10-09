function App() {
    const [token, setToken] = React.useState(null);
    const [view, setView] = React.useState('login');
    const [portalView, setPortalView] = React.useState('products'); // Vista inicial: lista de productos
    const [selectedProduct, setSelectedProduct] = React.useState(null);
    const [viewingContractId, setViewingContractId] = React.useState(null);

    const handleLoginSuccess = (newToken) => {
        setToken(newToken);
        setView('portal');
    };

    const handleProductSelect = (product) => {
        setSelectedProduct(product);
        setPortalView('simulator'); // Cambiar a la vista del simulador
    };

    const handleApplicationSuccess = () => {
        // Después de una solicitud exitosa, volver a la lista de solicitudes
        setPortalView('applications');
    };

    if (view === 'login') {
        return <LoginScreen onLoginSuccess={handleLoginSuccess} />;
    }

    if (viewingContractId) {
        return (
            <ContractView
                token={token}
                applicationId={viewingContractId}
                onBack={() => setViewingContractId(null)}
            />
        );
    }

    return (
        <React.Fragment>
            <header>
                <h1>Portal del Cliente</h1>
            </header>
            <Navbar setView={setPortalView} />
            <main>
                {portalView === 'products' && <ProductList token={token} onProductSelect={handleProductSelect} />}
                {portalView === 'simulator' && <LoanSimulator token={token} product={selectedProduct} onApplicationSuccess={handleApplicationSuccess} />}
                {portalView === 'applications' && <MyApplications token={token} onViewContract={setViewingContractId} />}
                {portalView === 'profile' && <Profile token={token} />}
            </main>
        </React.Fragment>
    );
}