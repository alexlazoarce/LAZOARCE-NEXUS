"""
backend/university_management_service.py

Servicio para el Módulo de Gestión Universitaria (LAN-UNV8).
"""
from .models import db, Student, DegreeProgram, Scholarship, StudentScholarship, LibraryResource, Alumnus
from sqlalchemy.exc import IntegrityError
from datetime import date

class UniversityManagementService:

    def update_student_admission_status(self, tenant_id, student_id, status):
        student = Student.query.filter_by(tenant_id=tenant_id, id=student_id).first()
        if not student:
            return None, "Estudiante no encontrado."

        allowed_statuses = ['Aplicante', 'Admitido', 'Rechazado', 'Egresado']
        if status not in allowed_statuses:
            return None, "Estado de admisión no válido."

        student.admission_status = status
        db.session.commit()
        return student, None

    def create_degree_program(self, tenant_id, data):
        program = DegreeProgram(
            name=data['name'],
            faculty=data.get('faculty'),
            credits_required=data.get('credits_required'),
            tenant_id=tenant_id
        )
        db.session.add(program)
        db.session.commit()
        return program

    def get_degree_programs(self, tenant_id):
        return DegreeProgram.query.filter_by(tenant_id=tenant_id).all()

    def create_scholarship(self, tenant_id, data):
        scholarship = Scholarship(
            name=data['name'],
            description=data.get('description'),
            amount_or_percentage=data['amount_or_percentage'],
            is_percentage=data.get('is_percentage', False),
            tenant_id=tenant_id
        )
        db.session.add(scholarship)
        db.session.commit()
        return scholarship

    def get_scholarships(self, tenant_id):
        return Scholarship.query.filter_by(tenant_id=tenant_id).all()

    def assign_scholarship_to_student(self, tenant_id, student_id, scholarship_id):
        try:
            assignment = StudentScholarship(
                student_id=student_id,
                scholarship_id=scholarship_id,
                tenant_id=tenant_id
            )
            db.session.add(assignment)
            db.session.commit()
            return assignment, None
        except IntegrityError:
            db.session.rollback()
            return None, "El estudiante ya tiene asignada esta beca."

    def get_student_scholarships(self, tenant_id, student_id):
        return StudentScholarship.query.filter_by(tenant_id=tenant_id, student_id=student_id).all()

    def create_library_resource(self, tenant_id, data):
        resource = LibraryResource(
            title=data['title'],
            author=data.get('author'),
            resource_type=data.get('resource_type'),
            url_or_identifier=data.get('url_or_identifier'),
            tenant_id=tenant_id
        )
        db.session.add(resource)
        db.session.commit()
        return resource

    def get_library_resources(self, tenant_id):
        return LibraryResource.query.filter_by(tenant_id=tenant_id).all()

    def graduate_student(self, tenant_id, student_id, graduation_date_str):
        student, error = self.update_student_admission_status(tenant_id, student_id, 'Egresado')
        if error:
            return None, error

        existing_alumnus = Alumnus.query.filter_by(student_id=student_id, tenant_id=tenant_id).first()
        if existing_alumnus:
            return None, "Este estudiante ya ha sido marcado como egresado."

        alumnus = Alumnus(
            student_id=student_id,
            graduation_date=date.fromisoformat(graduation_date_str) if graduation_date_str else date.today(),
            contact_email=student.user.email if student.user else None,
            tenant_id=tenant_id
        )
        db.session.add(alumnus)
        db.session.commit()
        return alumnus, None

university_management_service = UniversityManagementService()
