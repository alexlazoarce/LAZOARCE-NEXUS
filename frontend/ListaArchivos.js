const ListaArchivos = () => {
    const [archivos, setArchivos] = React.useState([]);

    React.useEffect(() => {
        // En el futuro, esto vendría de la API: fetch('/api/documentos')
        const datosDeEjemplo = [
            { id: 1, nombre: 'Contratos', tipo: 'carpeta', modificado: '2025-10-14 10:00' },
            { id: 2, nombre: 'Reportes Financieros', tipo: 'carpeta', modificado: '2025-10-12 08:30' },
            { id: 3, nombre: 'contrato_prestamo_001.pdf', tipo: 'archivo', modificado: '2025-10-14 09:45', tamano: '1.2 MB' },
            { id: 4, nombre: 'balance_general_q3.xlsx', tipo: 'archivo', modificado: '2025-10-11 15:20', tamano: '450 KB' },
            { id: 5, nombre: 'presentacion_inversores.pptx', tipo: 'archivo', modificado: '2025-10-10 11:05', tamano: '5.6 MB' },
        ];
        setArchivos(datosDeEjemplo);
    }, []);

    const fileIcon = (tipo) => {
        if (tipo === 'carpeta') return '📁';
        if (tipo === 'archivo') return '📄';
        return '❓';
    };

    const containerStyle = {
        fontFamily: 'Arial, sans-serif',
        border: '1px solid #ddd',
        borderRadius: '5px',
        padding: '10px'
    };

    const listStyle = {
        listStyleType: 'none',
        padding: 0
    };

    const listItemStyle = {
        display: 'flex',
        alignItems: 'center',
        padding: '10px',
        borderBottom: '1px solid #eee'
    };

    const iconStyle = {
        marginRight: '15px',
        fontSize: '20px'
    };

    const nameStyle = {
        flexGrow: 1,
        fontWeight: 'bold'
    };

    const metaStyle = {
        minWidth: '150px',
        color: '#888',
        fontSize: '14px'
    };


    return (
        <div style={containerStyle}>
            <ul style={listStyle}>
                {archivos.map(archivo => (
                    <li key={archivo.id} style={listItemStyle}>
                        <span style={iconStyle}>{fileIcon(archivo.tipo)}</span>
                        <span style={nameStyle}>{archivo.nombre}</span>
                        <span style={metaStyle}>{archivo.modificado}</span>
                        <span style={metaStyle}>{archivo.tamano || '--'}</span>
                    </li>
                ))}
            </ul>
        </div>
    );
};