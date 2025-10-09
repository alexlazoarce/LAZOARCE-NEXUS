function App() {
    const [token, setToken] = React.useState(null);
    const [userProfile, setUserProfile] = React.useState(null); // Guardar perfil del usuario
    const [view, setView] = React.useState('login');
    const [portalView, setPortalView] = React.useState('products');
    const [selectedProduct, setSelectedProduct] = React.useState(null);
    const [viewingContractId, setViewingContractId] = React.useState(null);
    const [viewingPaymentsForAppId, setViewingPaymentsForAppId] = React.useState(null);

    const fetchUserProfile = async (apiToken) => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/profile`, {
                headers: { 'Authorization': `Bearer ${apiToken}` }
            });
            const data = await res.json();
            if (res.ok) {
                setUserProfile(data);
            }
        } catch (error) {
            console.error("Error fetching user profile:", error);
        }
    };

    const handleLoginSuccess = (newToken) => {
        setToken(newToken);
        setView('portal');
        fetchUserProfile(newToken); // Obtener perfil al iniciar sesión
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
        return <ContractView token={token} applicationId={viewingContractId} onBack={() => setViewingContractId(null)} />;
    }

    if (viewingPaymentsForAppId) {
        return <PaymentHistory token={token} applicationId={viewingPaymentsForAppId} onBack={() => setViewingPaymentsForAppId(null)} />;
    }

    return (
        <React.Fragment>
            <header>
                <h1>Portal del Cliente</h1>
            </header>
            <Navbar setView={setPortalView} userRole={userProfile ? userProfile.role : null} />
            <main>
                {portalView === 'products' && <ProductList token={token} onProductSelect={handleProductSelect} />}
                {portalView === 'simulator' && <LoanSimulator token={token} product={selectedProduct} onApplicationSuccess={handleApplicationSuccess} />}
                {portalView === 'applications' && <MyApplications token={token} onViewContract={setViewingContractId} onViewPayments={setViewingPaymentsForAppId} />}
                {portalView === 'profile' && <Profile token={token} />}
                {portalView === 'journal' && <JournalView token={token} />}
                {portalView === 'rrhh' && (
                    <div>
                        <h2>Recursos Humanos</h2>
                        <EmployeeManagement token={token} />
                        <hr />
                        <PayrollView token={token} />
                    </div>
                )}
            </main>
        </React.Fragment>
    );
}