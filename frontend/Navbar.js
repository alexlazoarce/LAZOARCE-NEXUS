function Navbar({ setView }) {
    return (
        <nav className="navbar">
            <button onClick={() => setView('simulator')}>Simulador de Préstamos</button>
            <button onClick={() => setView('applications')}>Mis Solicitudes</button>
            <button onClick={() => setView('profile')}>Mi Perfil</button>
        </nav>
    );
}