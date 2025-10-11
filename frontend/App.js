function App() {
    const [token, setToken] = React.useState(localStorage.getItem('jwt_token'));
    const [userRoles, setUserRoles] = React.useState([]);
    const [view, setView] = React.useState('auth');
    const [loadingProfile, setLoadingProfile] = React.useState(true);

    const [viewingContractId, setViewingContractId] = React.useState(null);
    const [viewingPaySlipsForLogId, setViewingPaySlipsForLogId] = React.useState(null);
    const [managingPaymentsForApp, setManagingPaymentsForApp] = React.useState(null);

    const [accountingView, setAccountingView] = React.useState('journal');
    const [hrView, setHrView] = React.useState('employees');

    const fetchProfile = async (currentToken) => {
        if (!currentToken) {
            setUserRoles([]);
            setLoadingProfile(false);
            return;
        }
        try {
            setLoadingProfile(true);
            const response = await fetch(`${API_BASE_URL}/api/profile`, {
                headers: { 'Authorization': `Bearer ${currentToken}` }
            });
            if (response.status === 401) { handleLogout(); return; }
            if (!response.ok) throw new Error('Error al cargar perfil de usuario.');
            const data = await response.json();
            setUserRoles(data.roles || []);
        } catch (error) { console.error(error.message); setUserRoles([]); }
        finally { setLoadingProfile(false); }
    };

    React.useEffect(() => {
        const currentToken = localStorage.getItem('jwt_token');
        if (currentToken) {
            setToken(currentToken);
            fetchProfile(currentToken);
            setView('dashboard');
        } else {
            setView('auth');
            setLoadingProfile(false);
        }
    }, []);

    const handleLogin = (newToken) => {
        localStorage.setItem('jwt_token', newToken);
        setToken(newToken);
        fetchProfile(newToken);
        setView('dashboard');
    };

    const handleLogout = () => {
        localStorage.removeItem('jwt_token');
        setToken(null);
        setUserRoles([]);
        setView('auth');
        setViewingContractId(null);
        setViewingPaySlipsForLogId(null);
        setManagingPaymentsForApp(null);
    };

    const AccountingPortal = () => (
        <div>
            <nav>
                <button onClick={() => setAccountingView('journal')}>Libro Diario</button>
                <button onClick={() => setAccountingView('ledger')}>Libro Mayor</button>
                <button onClick={() => setAccountingView('trial_balance')}>Balanza</button>
                <button onClick={() => setAccountingView('balance_sheet')}>Balance General</button>
                <button onClick={() => setAccountingView('income_statement')}>Estado de Resultados</button>
            </nav>
            <hr />
            {accountingView === 'journal' && <JournalView token={token} />}
            {accountingView === 'ledger' && <GeneralLedgerView token={token} />}
            {accountingView === 'trial_balance' && <TrialBalanceView token={token} />}
            {accountingView === 'balance_sheet' && <BalanceSheetView token={token} />}
            {accountingView === 'income_statement' && <IncomeStatementView token={token} />}
        </div>
    );

    const HRPortal = () => {
        if (viewingPaySlipsForLogId) {
            return <PaySlipsView token={token} payrollLogId={viewingPaySlipsForLogId} onBack={() => setViewingPaySlipsForLogId(null)} />;
        }
        return (
            <div>
                <nav>
                    <button onClick={() => setHrView('employees')}>Gestión de Empleados</button>
                    <button onClick={() => setHrView('payroll')}>Procesar Nómina</button>
                </nav>
                <hr/>
                {hrView === 'employees' && <EmployeeManagement token={token} />}
                {hrView === 'payroll' && <PayrollView token={token} onViewPaySlips={setViewingPaySlipsForLogId} />}
            </div>
        );
    };

    const renderView = () => {
        if (loadingProfile) return <p>Cargando...</p>;
        if (!token || view === 'auth') return <Auth onLogin={handleLogin} />;

        if (viewingContractId) return <ContractView token={token} applicationId={viewingContractId} onBack={() => setViewingContractId(null)} />;
        if (managingPaymentsForApp) return <PaymentView token={token} application={managingPaymentsForApp} onBack={() => setManagingPaymentsForApp(null)} />;

        const isAdmin = userRoles.includes('Admin');
        const isContador = userRoles.includes('Contador');
        const isEjecutivo = userRoles.includes('Ejecutivo de Crédito');
        const isCobrador = userRoles.includes('Cobrador');

        switch (view) {
            case 'dashboard': return isAdmin ? <AdminDashboard token={token} onManagePayments={setManagingPaymentsForApp} /> : <MyApplications token={token} onViewContract={setViewingContractId} />;
            case 'products': return <LoanProducts token={token} />;
            case 'simulator': return <LoanSimulator token={token} />;
            case 'newApplication': return <LoanApplication token={token} onNavigate={setView} />;
            case 'accounting': return (isAdmin || isContador) ? <AccountingPortal /> : <p>Acceso no autorizado.</p>;
            case 'hr': return isAdmin ? <HRPortal /> : <p>Acceso no autorizado.</p>;
            case 'crm': return (isAdmin || isEjecutivo) ? <LeadManagementView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'collections': return (isAdmin || isCobrador) ? <PortfolioView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'templates': return isAdmin ? <TemplateManagerView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'audit': return isAdmin ? <AuditLogView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'testing': return isAdmin ? <TestingView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'profile': return <ProfileView token={token} />;
            default: return isAdmin ? <AdminDashboard token={token} onManagePayments={setManagingPaymentsForApp} /> : <MyApplications token={token} onViewContract={setViewingContractId} />;
        }
    };

    const NavigationView = () => {
        if (loadingProfile || !token || viewingContractId || viewingPaySlipsForLogId || managingPaymentsForApp) return null;
        const isAdmin = userRoles.includes('Admin');
        const isContador = userRoles.includes('Contador');
        const isEjecutivo = userRoles.includes('Ejecutivo de Crédito');
        const isCobrador = userRoles.includes('Cobrador');
        return (
            <nav>
                <button onClick={() => setView('dashboard')}>{isAdmin ? 'Panel de Admin' : 'Mis Solicitudes'}</button>
                {(isAdmin || isEjecutivo) && <button onClick={() => setView('crm')}>CRM</button>}
                {(isAdmin || isCobrador) && <button onClick={() => setView('collections')}>Cobranza</button>}
                <button onClick={() => setView('products')}>Productos</button>
                <button onClick={() => setView('simulator')}>Simulador</button>
                {!isAdmin && !isContador && !isEjecutivo && !isCobrador && <button onClick={() => setView('newApplication')}>Nueva Solicitud</button>}
                {(isAdmin || isContador) && <button onClick={() => setView('accounting')}>Contabilidad</button>}
                {isAdmin && <button onClick={() => setView('hr')}>RRHH</button>}
                {isAdmin && (
                    <div style={{border: '1px solid grey', padding: '5px', marginTop: '5px'}}>
                        <strong>Configuración:</strong>
                        <button onClick={() => setView('templates')}>Plantillas</button>
                        <button onClick={() => setView('audit')}>Auditoría</button>
                        <button onClick={() => setView('testing')}>Testing</button>
                    </div>
                )}
                <button onClick={() => setView('profile')}>Mi Perfil</button>
                <button onClick={handleLogout}>Cerrar Sesión</button>
            </nav>
        );
    };

    return (
        <div>
            <h1>LAZOARCE UNIVERSAL</h1>
            <NavigationView />
            <hr />
            <main>{renderView()}</main>
        </div>
    );
}