"""
backend/controller_service.py

Servicio para el Módulo de Contraloría (LAN-C7N).
"""
from .models import db, InternalControl, AuditReport
from sqlalchemy.exc import IntegrityError

class ControllerServiceManager:

    def create_internal_control(self, tenant_id, data):
        control = InternalControl(
            name=data['name'],
            description=data.get('description'),
            control_type=data.get('control_type'),
            frequency=data.get('frequency'),
            owner_id=data.get('owner_id'),
            tenant_id=tenant_id
        )
        db.session.add(control)
        db.session.commit()
        return control

    def get_internal_controls(self, tenant_id):
        return InternalControl.query.filter_by(tenant_id=tenant_id).all()

    def create_audit_report(self, tenant_id, data):
        report = AuditReport(
            title=data['title'],
            audit_area=data.get('audit_area'),
            findings=data.get('findings'),
            recommendations=data.get('recommendations'),
            report_date=data.get('report_date'),
            auditor_id=data.get('auditor_id'),
            tenant_id=tenant_id
        )
        db.session.add(report)
        db.session.commit()
        return report

    def get_audit_reports(self, tenant_id):
        return AuditReport.query.filter_by(tenant_id=tenant_id).all()

controller_service = ControllerServiceManager()
