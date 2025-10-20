from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.hr.models import Empleado, Nomina
from backend.hr.logic import generar_nomina_empleado, generar_boleta_pago
from datetime import datetime

hr_bp = Blueprint('hr_bp', __name__, url_prefix='/api/rrhh')

@hr_bp.route('/empleados', methods=['POST'])
def crear_empleado():
    data = request.get_json()
    try:
        nuevo_empleado = Empleado(
            codigo_empleado=data['codigo_empleado'],
            dui=data['dui'],
            nombre_completo=data['nombre_completo'],
            fecha_ingreso=datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date(),
            cargo=data['cargo'],
            salario_base=float(data['salario_base'])
        )
        db.session.add(nuevo_empleado)
        db.session.commit()
        return jsonify({"msg": "Empleado creado exitosamente", "id": nuevo_empleado.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@hr_bp.route('/empleados', methods=['GET'])
def get_empleados():
    empleados = Empleado.query.all()
    return jsonify([{"id": emp.id, "nombre": emp.nombre_completo, "codigo": emp.codigo_empleado} for emp in empleados])

@hr_bp.route('/nominas/generar', methods=['POST'])
def generar_nomina_endpoint():
    data = request.get_json()
    try:
        nomina = generar_nomina_empleado(
            empleado_id=data['empleado_id'],
            periodo=data['periodo'],
            horas_extra=data.get('horas_extra', 0),
            comisiones=data.get('comisiones', 0),
            bonificaciones=data.get('bonificaciones', 0)
        )
        db.session.commit()
        return jsonify({"msg": "Nómina generada exitosamente", "nomina_id": nomina.id, "asiento_id": nomina.asiento_contable_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@hr_bp.route('/nominas/<int:nomina_id>/boleta', methods=['GET'])
def get_boleta_pago(nomina_id):
    try:
        return generar_boleta_pago(nomina_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 404