"""
backend/data_protection_service.py

Servicio para el Módulo de Protección de Datos (LAN-DPR2).
"""
from .models import db, DataPrivacyRequest, User
from sqlalchemy.exc import IntegrityError
import json

class DataProtectionServiceManager:

    def create_request(self, tenant_id, user_id, request_type):
        request = DataPrivacyRequest(
            user_id=user_id,
            request_type=request_type,
            tenant_id=tenant_id
        )
        db.session.add(request)
        db.session.commit()
        return request

    def get_requests(self, tenant_id):
        return DataPrivacyRequest.query.filter_by(tenant_id=tenant_id).all()

    def process_request(self, tenant_id, request_id):
        request = DataPrivacyRequest.query.filter_by(id=request_id, tenant_id=tenant_id).first()
        if not request:
            return None

        if request.request_type == 'derecho_al_olvido':
            # Anonymize user data
            user = User.query.get(request.user_id)
            if user:
                user.email = f"anonymized_{user.id}@example.com"
                user.full_name = "Usuario Anonimizado"
                user.dui = None
                user.nit = None
                user.is_active = False
                db.session.commit()
            request.status = 'Procesada'
            request.completion_date = db.func.current_timestamp()
            db.session.commit()
            return request

        elif request.request_type == 'portabilidad':
            # Export user data to JSON
            user = User.query.get(request.user_id)
            if user:
                user_data = {
                    "full_name": user.full_name,
                    "email": user.email,
                    "dui": user.dui,
                    "nit": user.nit,
                }
                # Here you could add more data from other models
                request.status = 'Procesada'
                request.completion_date = db.func.current_timestamp()
                db.session.commit()
                return json.dumps(user_data, indent=4)

        return None

data_protection_service = DataProtectionServiceManager()
