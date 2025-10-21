const CashAndBanksView = () => {
    // Estado para cuentas bancarias y cajas chicas
    const [bankAccounts, setBankAccounts] = React.useState([]);
    const [cashBoxes, setCashBoxes] = React.useState([]);

    // Estado para la cuenta o caja seleccionada y sus transacciones
    const [selectedAccount, setSelectedAccount] = React.useState(null);
    const [selectedCashBox, setSelectedCashBox] = React.useState(null);
    const [transactions, setTransactions] = React.useState([]);

    // Estado para modales de creación
    const [showBankAccountModal, setShowBankAccountModal] = React.useState(false);
    const [showCashBoxModal, setShowCashBoxModal] = React.useState(false);
    const [showTransactionModal, setShowTransactionModal] = React.useState(false);

    const api = useApi();

    const fetchData = async () => {
        try {
            const accountsResponse = await api.get('/api/cash_and_banks/bank_accounts');
            setBankAccounts(accountsResponse.data || []);
            const cashBoxesResponse = await api.get('/api/cash_and_banks/cash_boxes');
            setCashBoxes(cashBoxesResponse.data || []);
        } catch (error) {
            console.error("Error fetching data:", error);
            alert('Error al cargar datos iniciales.');
        }
    };

    React.useEffect(() => {
        fetchData();
    }, []);

    const fetchTransactions = async (type, id) => {
        try {
            let url = '';
            if (type === 'bank') {
                url = `/api/cash_and_banks/bank_transactions/${id}`;
                setSelectedAccount(bankAccounts.find(acc => acc.id === id));
                setSelectedCashBox(null);
            } else { // cash
                url = `/api/cash_and_banks/cash_transactions/${id}`;
                setSelectedCashBox(cashBoxes.find(cb => cb.id === id));
                setSelectedAccount(null);
            }
            const response = await api.get(url);
            setTransactions(response.data || []);
        } catch (error) {
            console.error(`Error fetching transactions for ${type} ${id}:`, error);
            alert('Error al cargar transacciones.');
        }
    };

    const handleCreateBankAccount = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        try {
            await api.post('/api/cash_and_banks/bank_accounts', data);
            setShowBankAccountModal(false);
            fetchData(); // Recargar
            alert('Cuenta bancaria creada con éxito.');
        } catch (error) {
            console.error("Error creating bank account:", error);
            alert('Error al crear la cuenta bancaria.');
        }
    };

    const handleCreateCashBox = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        try {
            await api.post('/api/cash_and_banks/cash_boxes', data);
            setShowCashBoxModal(false);
            fetchData(); // Recargar
            alert('Caja chica creada con éxito.');
        } catch (error) {
            console.error("Error creating cash box:", error);
            alert('Error al crear la caja chica.');
        }
    };

    const handleCreateTransaction = async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());

        let url = '';
        if (selectedAccount) {
            url = '/api/cash_and_banks/bank_transactions';
            data.bank_account_id = selectedAccount.id;
        } else if (selectedCashBox) {
            url = '/api/cash_and_banks/cash_transactions';
            data.cash_box_id = selectedCashBox.id;
        }

        try {
            await api.post(url, data);
            setShowTransactionModal(false);
            fetchTransactions(selectedAccount ? 'bank' : 'cash', selectedAccount ? selectedAccount.id : selectedCashBox.id);
            alert('Transacción creada con éxito.');
        } catch (error) {
            console.error("Error creating transaction:", error);
            alert('Error al crear la transacción.');
        }
    };

    return (
        <div className="container-fluid">
            <h1>Gestión de Caja y Bancos (LAN-CB2)</h1>
            <p>Este módulo permite registrar movimientos de caja chica, conciliación bancaria, transferencias y cheques.</p>

            <div className="row">
                {/* Column for Bank Accounts */}
                <div className="col-md-3">
                    <div className="card">
                        <div className="card-header d-flex justify-content-between align-items-center">
                            Cuentas Bancarias
                            <button className="btn btn-sm btn-primary" onClick={() => setShowBankAccountModal(true)}>+</button>
                        </div>
                        <ul className="list-group list-group-flush">
                            {bankAccounts.map(acc => (
                                <li key={acc.id} className={`list-group-item list-group-item-action ${selectedAccount?.id === acc.id ? 'active' : ''}`} onClick={() => fetchTransactions('bank', acc.id)}>
                                    {acc.account_name} ({acc.bank_name})
                                </li>
                            ))}
                        </ul>
                    </div>
                     <div className="card mt-3">
                        <div className="card-header d-flex justify-content-between align-items-center">
                            Cajas Chicas
                            <button className="btn btn-sm btn-primary" onClick={() => setShowCashBoxModal(true)}>+</button>
                        </div>
                        <ul className="list-group list-group-flush">
                           {cashBoxes.map(cb => (
                                <li key={cb.id} className={`list-group-item list-group-item-action ${selectedCashBox?.id === cb.id ? 'active' : ''}`} onClick={() => fetchTransactions('cash', cb.id)}>
                                    {cb.box_name}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Column for Transactions */}
                <div className="col-md-9">
                    <div className="card">
                        <div className="card-header d-flex justify-content-between align-items-center">
                           <span>Transacciones de: <strong>{selectedAccount?.account_name || selectedCashBox?.box_name || 'Ninguna seleccionada'}</strong></span>
                           {(selectedAccount || selectedCashBox) && (
                               <button className="btn btn-sm btn-success" onClick={() => setShowTransactionModal(true)}>Nueva Transacción</button>
                           )}
                        </div>
                        <div className="card-body">
                           {transactions.length > 0 ? (
                               <table className="table table-striped">
                                   <thead>
                                       <tr>
                                           <th>Fecha</th>
                                           <th>Tipo</th>
                                           <th>Descripción</th>
                                           <th className="text-end">Monto</th>
                                       </tr>
                                   </thead>
                                   <tbody>
                                       {transactions.map(t => (
                                           <tr key={t.id}>
                                               <td>{new Date(t.transaction_date).toLocaleDateString()}</td>
                                               <td>{t.transaction_type}</td>
                                               <td>{t.description}</td>
                                               <td className={`text-end ${t.transaction_type === 'Egreso' ? 'text-danger' : 'text-success'}`}>
                                                   ${parseFloat(t.amount).toFixed(2)}
                                               </td>
                                           </tr>
                                       ))}
                                   </tbody>
                               </table>
                           ) : (
                               <p>Seleccione una cuenta o caja para ver sus transacciones o registre una nueva.</p>
                           )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Modals */}
            {showBankAccountModal && (
                <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <form onSubmit={handleCreateBankAccount}>
                                <div className="modal-header">
                                    <h5 className="modal-title">Nueva Cuenta Bancaria</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowBankAccountModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <div className="mb-3">
                                        <label htmlFor="account_name" className="form-label">Nombre de la Cuenta</label>
                                        <input type="text" className="form-control" id="account_name" name="account_name" required />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="account_number" className="form-label">Número de Cuenta</label>
                                        <input type="text" className="form-control" id="account_number" name="account_number" required />
                                    </div>
                                     <div className="mb-3">
                                        <label htmlFor="bank_name" className="form-label">Nombre del Banco</label>
                                        <input type="text" className="form-control" id="bank_name" name="bank_name" required />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="initial_balance" className="form-label">Saldo Inicial</label>
                                        <input type="number" step="0.01" className="form-control" id="initial_balance" name="initial_balance" defaultValue="0" />
                                    </div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowBankAccountModal(false)}>Cerrar</button>
                                    <button type="submit" className="btn btn-primary">Crear Cuenta</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}

            {showCashBoxModal && (
                 <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                             <form onSubmit={handleCreateCashBox}>
                                <div className="modal-header">
                                    <h5 className="modal-title">Nueva Caja Chica</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowCashBoxModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                    <div className="mb-3">
                                        <label htmlFor="box_name" className="form-label">Nombre de la Caja</label>
                                        <input type="text" className="form-control" id="box_name" name="box_name" required />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="initial_balance" className="form-label">Saldo Inicial</label>
                                        <input type="number" step="0.01" className="form-control" id="initial_balance" name="initial_balance" defaultValue="0" />
                                    </div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowCashBoxModal(false)}>Cerrar</button>
                                    <button type="submit" className="btn btn-primary">Crear Caja</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}

            {showTransactionModal && (
                <div className="modal show" tabIndex="-1" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <form onSubmit={handleCreateTransaction}>
                                <div className="modal-header">
                                    <h5 className="modal-title">Nueva Transacción para {selectedAccount?.account_name || selectedCashBox?.box_name}</h5>
                                    <button type="button" className="btn-close" onClick={() => setShowTransactionModal(false)}></button>
                                </div>
                                <div className="modal-body">
                                     <div className="mb-3">
                                        <label htmlFor="transaction_type" className="form-label">Tipo de Transacción</label>
                                        <select className="form-select" id="transaction_type" name="transaction_type" required>
                                            <option value="Ingreso">Ingreso</option>
                                            <option value="Egreso">Egreso</option>
                                        </select>
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="amount" className="form-label">Monto</label>
                                        <input type="number" step="0.01" className="form-control" id="amount" name="amount" required />
                                    </div>
                                    <div className="mb-3">
                                        <label htmlFor="description" className="form-label">Descripción</label>
                                        <textarea className="form-control" id="description" name="description" rows="2"></textarea>
                                    </div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowTransactionModal(false)}>Cerrar</button>
                                    <button type="submit" className="btn btn-primary">Guardar Transacción</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
