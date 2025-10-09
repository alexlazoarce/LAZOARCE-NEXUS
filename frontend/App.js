function App() {
    // Estado para gestionar si el usuario está logueado y su token
    const [token, setToken] = React.useState(null);
    // Estado para gestionar la vista principal (login o el portal)
    const [view, setView] = React.useState('login');
    // Estado para gestionar la vista dentro del portal
    const [portalView, setPortalView] = React.useState('simulator');

    const handleLoginSuccess = (newToken) => {
        setToken(newToken);
        setView('portal'); // Cambiar a la vista del portal al iniciar sesión
    };

    // Renderizado condicional basado en el estado `view`
    if (view === 'login') {
        // Pasamos la función de éxito al componente de login/simulador
        return <LoginScreen onLoginSuccess={handleLoginSuccess} />;
    }

    return (
        <React.Fragment>
            <header>
                <h1>Portal del Cliente</h1>
            </header>
            <Navbar setView={setPortalView} />
            <main>
                {/* Renderizar el componente correcto dentro del portal */}
                {portalView === 'simulator' && <LoanSimulator token={token} />}
                {portalView === 'applications' && <MyApplications token={token} />}
            </main>
        </React.Fragment>
    );
}