function Navbar({ setView, userRole }) {
    const isAdminOrAccountant = userRole === 'Administrador General' || userRole === 'Contador' || userRole === 'Super Administrador';

    return (
        <nav className="navbar">
            <button onClick={() => setView('products')}>Productos</button>
            <button onClick={() => setView('applications')}>Mis Solicitudes</button>
            <button onClick={() => setView('profile')}>Mi Perfil</button>
            {isAdminOrAccountant && (
                <button onClick={() => setView('journal')}>Libro Diario</button>
            )}
        </nav>
    );
}