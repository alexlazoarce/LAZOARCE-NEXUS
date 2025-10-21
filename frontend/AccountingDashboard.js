// frontend/AccountingDashboard.js

function AccountingDashboard() {
    return (
        '<div>' +
        '<h2>Panel de Contabilidad</h2>' +
        '<p>Seleccione un reporte para visualizar:</p>' +
        '<ul>' +
        '<li><a href="#" onClick={() => onNavigate("balance-sheet")}>Balance General</a></li>' +
        '<li><a href="#" onClick={() => onNavigate("income-statement")}>Estado de Resultados</a></li>' +
        '</ul>' +
        '</div>'
    );
}
