const EducationView = () => {
    const [students, setStudents] = React.useState([]);
    const [courses, setCourses] = React.useState([]);
    const [view, setView] = React.useState('students'); // students | courses

    const [showStudentModal, setShowStudentModal] = React.useState(false);
    const [showCourseModal, setShowCourseModal] = React.useState(false);

    const api = useApi();

    const fetchData = async () => {
        try {
            const studentsResponse = await api.get('/api/education/students');
            setStudents(studentsResponse.data || []);
            const coursesResponse = await api.get('/api/education/courses');
            setCourses(coursesResponse.data || []);
        } catch (error) {
            console.error("Error fetching education data:", error);
            alert('Error al cargar los datos de educación.');
        }
    };

    React.useEffect(() => {
        fetchData();
    }, []);

    const handleCreateStudent = async (event) => {
        event.preventDefault();
        const data = Object.fromEntries(new FormData(event.target).entries());
        try {
            await api.post('/api/education/students', data);
            setShowStudentModal(false);
            fetchData();
            alert('Estudiante creado con éxito.');
        } catch (error) {
            console.error("Error creating student:", error);
            alert('Error al crear el estudiante.');
        }
    };

    const handleCreateCourse = async (event) => {
        event.preventDefault();
        const data = Object.fromEntries(new FormData(event.target).entries());
        try {
            await api.post('/api/education/courses', data);
            setShowCourseModal(false);
            fetchData();
            alert('Curso creado con éxito.');
        } catch (error) {
            console.error("Error creating course:", error);
            alert('Error al crear el curso.');
        }
    };

    const renderStudentsView = () => (
        <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
                Estudiantes
                <button className="btn btn-sm btn-primary" onClick={() => setShowStudentModal(true)}>Nuevo Estudiante</button>
            </div>
            <div className="card-body">
                <table className="table table-striped">
                    <thead><tr><th>ID</th><th>Código</th><th>Nombre Completo</th></tr></thead>
                    <tbody>
                        {students.map(s => <tr key={s.id}><td>{s.id}</td><td>{s.student_code}</td><td>{s.full_name}</td></tr>)}
                    </tbody>
                </table>
            </div>
        </div>
    );

    const renderCoursesView = () => (
        <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
                Cursos
                <button className="btn btn-sm btn-primary" onClick={() => setShowCourseModal(true)}>Nuevo Curso</button>
            </div>
            <div className="card-body">
                <table className="table table-striped">
                    <thead><tr><th>ID</th><th>Código</th><th>Nombre del Curso</th><th>Profesor</th></tr></thead>
                    <tbody>
                        {courses.map(c => <tr key={c.id}><td>{c.id}</td><td>{c.course_code}</td><td>{c.name}</td><td>{c.teacher_name}</td></tr>)}
                    </tbody>
                </table>
            </div>
        </div>
    );

    return (
        <div className="container-fluid">
            <h1>Gestión de Educación (LAN-ED3U)</h1>
            <p>Matrículas, pagos, calificaciones, horarios y certificados.</p>

            <ul className="nav nav-tabs">
                <li className="nav-item"><a className={`nav-link ${view === 'students' ? 'active' : ''}`} href="#" onClick={() => setView('students')}>Estudiantes</a></li>
                <li className="nav-item"><a className={`nav-link ${view === 'courses' ? 'active' : ''}`} href="#" onClick={() => setView('courses')}>Cursos</a></li>
            </ul>

            <div className="mt-3">
                {view === 'students' ? renderStudentsView() : renderCoursesView()}
            </div>

            {/* Modals */}
            {showStudentModal && (
                <div className="modal show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}><div className="modal-dialog">
                    <div className="modal-content">
                        <form onSubmit={handleCreateStudent}>
                            <div className="modal-header"><h5 className="modal-title">Nuevo Estudiante</h5><button type="button" className="btn-close" onClick={() => setShowStudentModal(false)}></button></div>
                            <div className="modal-body">
                                <div className="mb-3"><label className="form-label">Nombre Completo</label><input type="text" className="form-control" name="full_name" required /></div>
                                <div className="mb-3"><label className="form-label">Código de Estudiante</label><input type="text" className="form-control" name="student_code" /></div>
                            </div>
                            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowStudentModal(false)}>Cerrar</button><button type="submit" className="btn btn-primary">Guardar</button></div>
                        </form>
                    </div>
                </div></div>
            )}
             {showCourseModal && (
                <div className="modal show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}><div className="modal-dialog">
                    <div className="modal-content">
                        <form onSubmit={handleCreateCourse}>
                            <div className="modal-header"><h5 className="modal-title">Nuevo Curso</h5><button type="button" className="btn-close" onClick={() => setShowCourseModal(false)}></button></div>
                            <div className="modal-body">
                                <div className="mb-3"><label className="form-label">Nombre del Curso</label><input type="text" className="form-control" name="name" required /></div>
                                <div className="mb-3"><label className="form-label">Código del Curso</label><input type="text" className="form-control" name="course_code" /></div>
                                <div className="mb-3"><label className="form-label">ID del Profesor (Usuario)</label><input type="number" className="form-control" name="teacher_id" /></div>
                            </div>
                            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowCourseModal(false)}>Cerrar</button><button type="submit" className="btn btn-primary">Guardar</button></div>
                        </form>
                    </div>
                </div></div>
            )}
        </div>
    );
};
