"""
backend/school_management_service.py

Servicio para el Módulo de Gestión Escolar (LAN-SCH6).
"""
from .models import db, Student, Course, Enrollment, Grade, TuitionPayment, User
from sqlalchemy.exc import IntegrityError

class SchoolManagementService:

    def get_students(self, tenant_id):
        return Student.query.filter_by(tenant_id=tenant_id).all()

    def get_student_by_id(self, tenant_id, student_id):
        return Student.query.filter_by(tenant_id=tenant_id, id=student_id).first()

    def create_student(self, tenant_id, data):
        try:
            student = Student(
                full_name=data['full_name'],
                student_code=data.get('student_code'),
                tenant_id=tenant_id,
                user_id=data.get('user_id')
            )
            db.session.add(student)
            db.session.commit()
            return student
        except IntegrityError:
            db.session.rollback()
            return None

    def get_courses(self, tenant_id):
        return Course.query.filter_by(tenant_id=tenant_id).all()

    def get_course_by_id(self, tenant_id, course_id):
        return Course.query.filter_by(tenant_id=tenant_id, id=course_id).first()

    def create_course(self, tenant_id, data):
        try:
            course = Course(
                name=data['name'],
                course_code=data.get('course_code'),
                teacher_id=data.get('teacher_id'),
                tenant_id=tenant_id
            )
            db.session.add(course)
            db.session.commit()
            return course
        except IntegrityError:
            db.session.rollback()
            return None

    def enroll_student(self, tenant_id, student_id, course_id):
        student = self.get_student_by_id(tenant_id, student_id)
        course = self.get_course_by_id(tenant_id, course_id)
        if not student or not course:
            return None, "Estudiante o curso no encontrado."

        existing_enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course_id, tenant_id=tenant_id).first()
        if existing_enrollment:
            return None, "El estudiante ya está inscrito en este curso."

        try:
            enrollment = Enrollment(
                student_id=student_id,
                course_id=course_id,
                tenant_id=tenant_id
            )
            db.session.add(enrollment)
            db.session.commit()
            return enrollment, None
        except IntegrityError as e:
            db.session.rollback()
            return None, f"Error de base de datos: {e}"

    def get_student_enrollments(self, tenant_id, student_id):
        return Enrollment.query.filter_by(tenant_id=tenant_id, student_id=student_id).all()

    def add_grade(self, tenant_id, enrollment_id, data):
        enrollment = Enrollment.query.filter_by(id=enrollment_id, tenant_id=tenant_id).first()
        if not enrollment:
            return None, "Inscripción no encontrada."

        grade = Grade(
            enrollment_id=enrollment_id,
            grade_name=data['grade_name'],
            score=data['score'],
            tenant_id=tenant_id
        )
        db.session.add(grade)
        db.session.commit()

        # Opcional: Recalcular nota final
        self.update_final_grade(enrollment)

        return grade, None

    def update_final_grade(self, enrollment):
        # Lógica para promediar las notas y actualizar final_grade en Enrollment
        total_score = sum(g.score for g in enrollment.grades)
        count = len(enrollment.grades.all())
        if count > 0:
            enrollment.final_grade = total_score / count
            db.session.commit()

    def add_tuition_payment(self, tenant_id, student_id, data):
        student = self.get_student_by_id(tenant_id, student_id)
        if not student:
            return None, "Estudiante no encontrado."

        payment = TuitionPayment(
            student_id=student_id,
            amount=data['amount'],
            payment_date=data.get('payment_date'),
            concept=data.get('concept'),
            tenant_id=tenant_id
        )
        db.session.add(payment)
        db.session.commit()
        return payment, None

    def get_student_payments(self, tenant_id, student_id):
        return TuitionPayment.query.filter_by(tenant_id=tenant_id, student_id=student_id).all()

school_management_service = SchoolManagementService()
