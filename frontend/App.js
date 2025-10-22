import React from 'react';
// Asumiendo que las importaciones de todos los componentes existen
// import Auth from './components/Auth';
// import AdminDashboard from './components/AdminDashboard';
// ... otros imports ...
// import EducationView from './components/EducationView';
// import FieldOperationsView from './components/FieldOperationsView';
// import TechnicalServiceView from './components/TechnicalServiceView';

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
    const [crmView, setCrmView] = React.useState('leads');
    const [marketingView, setMarketingView] = React.useState('campaigns');
    const [constructionView, setConstructionView] = React.useState('projects'); // Estado para ConstructionView
    const API_BASE_URL = 'http://localhost:5000'; // Ajusta según sea necesario

    // Función para obtener el perfil del usuario
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
            if (response.status === 401) { // No autorizado o token expirado
                handleLogout();
                return;
            }
            if (!response.ok) throw new Error('Error al cargar perfil de usuario.');
            const data = await response.json();
            setUserRoles(data.roles || []); // Asegura que roles sea siempre un array
        } catch (error) {
            console.error(error.message);
            setUserRoles([]); // Resetea roles en caso de error
        } finally {
            setLoadingProfile(false);
        }
    };

    // Efecto para cargar el perfil al montar el componente si hay token
    React.useEffect(() => {
        const currentToken = localStorage.getItem('jwt_token');
        if (currentToken) {
            setToken(currentToken);
            fetchProfile(currentToken);
            setView('dashboard'); // Vista por defecto para usuarios logueados
        } else {
            setView('auth'); // Muestra vista de autenticación si no hay token
            setLoadingProfile(false); // No hay perfil que cargar
        }
    }, []); // Array vacío = ejecutar solo al montar

    // Manejador para el login
    const handleLogin = (newToken) => {
        localStorage.setItem('jwt_token', newToken);
        setToken(newToken);
        fetchProfile(newToken); // Obtener perfil después del login
        setView('dashboard'); // Navegar al dashboard
    };

    // Manejador para el logout
    const handleLogout = () => {
        localStorage.removeItem('jwt_token');
        setToken(null);
        setUserRoles([]);
        setView('auth'); // Navegar a la vista de autenticación
        // Resetear estados específicos de vistas detalladas
        setViewingContractId(null);
        setViewingPaySlipsForLogId(null);
        setManagingPaymentsForApp(null);
    };

    // --- Sub-portales para módulos ---
    const AccountingPortal = () => (
        <div>
            <nav>
                <button onClick={() => setAccountingView('journal')}>Libro Diario</button>
                <button onClick={() => setAccountingView('income_statement')}>Estado de Resultados</button>
            </nav>
            <hr />
            {accountingView === 'journal' && <JournalView token={token} />}
            {accountingView === 'income_statement' && <IncomeStatementView token={token} />}
        </div>
    );

    const HRPortal = () => {
        if (viewingPaySlipsForLogId) return <PaySlipsView token={token} payrollLogId={viewingPaySlipsForLogId} onBack={() => setViewingPaySlipsForLogId(null)} />;
        return (
            <div>
                <nav>
                    <button onClick={() => setHrView('employees')}>Gestión de Empleados</button>
                    <button onClick={() => setHrView('payroll')}>Procesar Nómina</button>
                </nav>
                <hr />
                {hrView === 'employees' && <EmployeeManagement token={token} />}
                {hrView === 'payroll' && <PayrollView token={token} onViewPaySlips={setViewingPaySlipsForLogId} />}
            </div>
        );
    };

    const CRMPortal = () => (
        <div>
            <nav>
                <button onClick={() => setCrmView('leads')}>Leads</button>
                <button onClick={() => setCrmView('opportunities')}>Oportunidades</button>
            </nav>
            <hr />
            {crmView === 'leads' && <LeadManagementView token={token} />}
            {crmView === 'opportunities' && <OpportunityPipelineView token={token} />}
        </div>
    );

    const MarketingPortal = () => (
        <div>
            <nav>
                <button onClick={() => setMarketingView('lists')}>Listas de Correo</button>
                <button onClick={() => setMarketingView('campaigns')}>Campañas</button>
            </nav>
            <hr />
            {marketingView === 'lists' && <MailingListView token={token} />}
            {marketingView === 'campaigns' && <CampaignView token={token} />}
        </div>
    );

    const ConstructionPortal = () => (
        <div>
            <nav>
                <button onClick={() => setConstructionView('projects')}>Proyectos</button>
                <button onClick={() => setConstructionView('budget_items')}>Ítems de Presupuesto</button>
                <button onClick={() => setConstructionView('progress_reports')}>Reportes de Progreso</button>
                <button onClick={() => setConstructionView('certifications')}>Certificaciones</button>
                <button onClick={() => setConstructionView('rfis')}>RFIs</button>
                <button onClick={() => setConstructionView('milestones')}>Hitos</button>
            </nav>
            <hr />
            {constructionView === 'projects' && <ConstructionProjectsView token={token} />}
            {constructionView === 'budget_items' && <BudgetItemsView token={token} />}
            {constructionView === 'progress_reports' && <ProgressReportsView token={token} />}
            {constructionView === 'certifications' && <CertificationsView token={token} />}
            {constructionView === 'rfis' && <RFIsView token={token} />}
            {constructionView === 'milestones' && <MilestonesView token={token} />}
        </div>
    );

    // --- Lógica principal de renderizado de vistas ---
    const renderView = () => {
        if (loadingProfile) return <p>Cargando...</p>;
        if (!token || view === 'auth') return <Auth onLogin={handleLogin} />;
        if (viewingContractId) return <ContractView token={token} applicationId={viewingContractId} onBack={() => setViewingContractId(null)} />;
        if (managingPaymentsForApp) return <PaymentView token={token} application={managingPaymentsForApp} onBack={() => setManagingPaymentsForApp(null)} />;
        const isAdmin = userRoles.includes('Admin') || userRoles.includes('Administrador General');
        const isContador = userRoles.includes('Contador');
        const isEjecutivo = userRoles.includes('Ejecutivo de Crédito');
        const isCobrador = userRoles.includes('Cobrador');
        const isSupport = userRoles.includes('Soporte');
        switch (view) {
            case 'dashboard': return isAdmin ? <AdminDashboard token={token} onManagePayments={setManagingPaymentsForApp} /> : <MyApplications token={token} onViewContract={setViewingContractId} />;
            case 'products': return <LoanProducts token={token} />;
            case 'simulator': return <LoanSimulator token={token} />;
            case 'newApplication': return <LoanApplication token={token} onNavigate={setView} />;
            case 'accounting': return (isAdmin || isContador) ? <AccountingPortal /> : <p>Acceso no autorizado.</p>;
            case 'cash_and_banks': return (isAdmin || isContador) ? <CashAndBanksView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'tax': return (isAdmin || isContador) ? <TaxView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'materials': return isAdmin ? <MaterialManagementView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'construction': return isAdmin ? <ConstructionPortal /> : <p>Acceso no autorizado.</p>;
            case 'health': return isAdmin ? <HealthView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'education': return isAdmin ? <EducationView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'logistics': return isAdmin ? <LogisticsView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'restaurant': return isAdmin ? <RestaurantView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'commercial_kitchen': return isAdmin ? <CommercialKitchenView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'field_ops': return isAdmin ? <FieldOperationsView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'technical_services': return isAdmin ? <TechnicalServiceView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'hr': return isAdmin ? <HRPortal /> : <p>Acceso no autorizado.</p>;
            case 'crm': return (isAdmin || isEjecutivo) ? <CRMPortal /> : <p>Acceso no autorizado.</p>;
            case 'collections': return (isAdmin || isCobrador) ? <PortfolioView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'marketing': return isAdmin ? <MarketingPortal /> : <p>Acceso no autorizado.</p>;
            case 'support': return (isAdmin || isSupport) ? <SupportDashboardView token={token} /> : <ClientTicketsView token={token} />;
            case 'templates': return isAdmin ? <TemplateManagerView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'audit': return isAdmin ? <AuditLogView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'testing': return isAdmin ? <TestingView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'school_management': return isAdmin ? <SchoolManagementView token={token} /> : <p>Acceso no autorizado.</p>;
            case 'profile': return <ProfileView token={token} />;
            default: return isAdmin ? <AdminDashboard token={token} onManagePayments={setManagingPaymentsForApp} /> : <MyApplications token={token} onViewContract={setViewingContractId} />;
        }
    };

    // --- Componente de Navegación ---
    const NavigationView = () => {
        if (loadingProfile || !token || view === 'auth' || viewingContractId || viewingPaySlipsForLogId || managingPaymentsForApp) return null;
        const isAdmin = userRoles.includes('Admin') || userRoles.includes('Administrador General');
        const isContador = userRoles.includes('Contador');
        const isEjecutivo = userRoles.includes('Ejecutivo de Crédito');
        const isCobrador = userRoles.includes('Cobrador');
        const isSupport = userRoles.includes('Soporte');
        return (
            <nav>
                {/* Módulos Comunes */}
                <button onClick={() => setView('dashboard')}>{isAdmin ? 'Panel de Admin' : 'Mis Solicitudes'}</button>
                <button onClick={() => setView('support')}>Soporte</button>
                <button onClick={() => setView('products')}>Productos</button>
                <button onClick={() => setView('simulator')}>Simulador</button>
                {!isAdmin && !isContador && !isEjecutivo && !isCobrador && !isSupport && <button onClick={() => setView('newApplication')}>Nueva Solicitud</button>}
                {/* Módulos Específicos por Rol */}
                {(isAdmin || isEjecutivo) && <button onClick={() => setView('crm')}>CRM</button>}
                {(isAdmin || isCobrador) && <button onClick={() => setView('collections')}>Cobranza</button>}
                {(isAdmin || isContador) && <button onClick={() => setView('accounting')}>Contabilidad</button>}
                {(isAdmin || isContador) && <button onClick={() => setView('cash_and_banks')}>Caja y Bancos</button>}
                {(isAdmin || isContador) && <button onClick={() => setView('tax')}>Impuestos</button>}
                {isAdmin && <button onClick={() => setView('marketing')}>Marketing</button>}
                {isAdmin && <button onClick={() => setView('materials')}>Recursos Materiales</button>}
                {isAdmin && <button onClick={() => setView('construction')}>Obras y Construcción</button>}
                {isAdmin && <button onClick={() => setView('health')}>Salud</button>}
                {isAdmin && <button onClick={() => setView('education')}>Educación</button>}
                {isAdmin && <button onClick={() => setView('logistics')}>Logística</button>}
                {isAdmin && <button onClick={() => setView('restaurant')}>Restaurantes</button>}
                {isAdmin && <button onClick={() => setView('commercial_kitchen')}>Cocina Comercial</button>}
                {isAdmin && <button onClick={() => setView('field_ops')}>Operaciones de Campo</button>}
                {isAdmin && <button onClick={() => setView('technical_services')}>Servicios Técnicos</button>}
                {isAdmin && <button onClick={() => setView('school_management')}>Gestión Escolar</button>}
                {isAdmin && <button onClick={() => setView('hr')}>RRHH</button>}
                {isAdmin && (
                    <div style={{ border: '1px solid grey', padding: '5px', marginTop: '5px' }}>
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

    // --- Renderizado Principal ---
    return (
        <div>
            <h1>LAZOARCE UBMS | Universal Business Management System</h1>
            <NavigationView />
            <hr />
            <main>{renderView()}</main>
        </div>
    );
}

export default App;