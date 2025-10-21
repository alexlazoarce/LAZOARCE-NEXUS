import re
import hashlib
import uuid
from datetime import datetime, timedelta
from flask import request
from .database import db
from .models import Cliente, ContratoIntegracion, FirmaElectronica, CertificadoValidacion
import random

def generar_contrato_integracion(datos_cliente):
    """
    Generar contrato de integración completo desde una plantilla.
    """
    try:
        contrato_id = f"CON-INT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

        with open('backend/templates/contrato_integracion.html', 'r', encoding='utf-8') as f:
            contrato_html_template = f.read()

        contrato_html = contrato_html_template.format(
            contrato_id=contrato_id,
            nombre_completo=datos_cliente['nombre_completo'],
            dui=datos_cliente['dui'],
            email=datos_cliente['email'],
            telefono=datos_cliente['telefono'],
            direccion=datos_cliente['direccion'],
            fecha_actual=datetime.now().strftime('%d/%m/%Y')
        )

        contrato = ContratoIntegracion(
            contrato_id=contrato_id,
            cliente_dui=datos_cliente['dui'],
            cliente_nombre=datos_cliente['nombre_completo'],
            cliente_email=datos_cliente['email'],
            contrato_html=contrato_html,
            estado="PENDIENTE_FIRMA"
        )

        db.session.add(contrato)
        db.session.commit()

        print(f"✅ CONTRATO GENERADO: {contrato_id}")
        return contrato_id

    except Exception as e:
        print(f"❌ ERROR generando contrato: {str(e)}")
        return None

def validacion_identidad_estricta(datos_cliente):
    """
    Validación rigurosa de identidad del cliente
    """
    try:
        print("=== VALIDACIÓN DE IDENTIDAD ===")

        # 1. Validar formato DUI
        if not re.match(r'^\d{8}-\d{1}$', datos_cliente['dui']):
            print("❌ Formato DUI inválido")
            return False

        # 2. Validar dígito verificador DUI
        if not validar_digito_verificador_dui(datos_cliente['dui']):
            print("❌ DUI inválido - dígito verificador incorrecto")
            return False

        # 3. Validar email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', datos_cliente['email']):
            print("❌ Email inválido")
            return False

        # 4. Validar teléfono
        if not re.match(r'^[267]\d{3}-\d{4}$', datos_cliente['telefono']):
            print("❌ Formato teléfono inválido (formato: 2XXX-XXXX)")
            return False

        # 5. Verificar duplicados
        if Cliente.query.filter_by(dui=datos_cliente['dui']).first():
            print("❌ Cliente ya existe con este DUI")
            return False

        if Cliente.query.filter_by(email=datos_cliente['email']).first():
            print("❌ Cliente ya existe con este email")
            return False

        print("✅ VALIDACIÓN DE IDENTIDAD EXITOSA")
        return True

    except Exception as e:
        print(f"❌ ERROR en validación: {str(e)}")
        return False

def validar_digito_verificador_dui(dui):
    """
    Validar dígito verificador de DUI salvadoreño
    """
    try:
        partes = dui.split('-')
        numero = partes[0]
        digito_verificador = int(partes[1])

        # Algoritmo de validación DUI
        suma = 0
        factores = [9, 8, 7, 6, 5, 4, 3, 2]

        for i in range(8):
            suma += int(numero[i]) * factores[i]

        residuo = suma % 10
        digito_calculado = 10 - residuo if residuo != 0 else 0

        return digito_calculado == digito_verificador

    except:
        return False

def capturar_datos_biometricos():
    """
    Simular captura de datos biométricos
    En producción, integrar con APIs de biometría
    """
    try:
        datos_biometricos = {
            # Hash de template facial (simulado)
            'hash_facial': hashlib.sha256(f"facial_{datetime.now().timestamp()}".encode()).hexdigest(),

            # Datos de dispositivo
            'dispositivo_id': str(uuid.uuid4()),
            'tipo_dispositivo': 'webcam',

            # Timestamps
            'timestamp_captura': datetime.now().isoformat(),
            'score_confianza': 95.5,  # Score de confianza biométrica

            # Metadata
            'resolucion_imagen': '1280x720',
            'luminosidad_promedio': 65.2,
            'numero_puntos_faciales': 128
        }

        print("✅ DATOS BIOMÉTRICOS CAPTURADOS")
        return datos_biometricos

    except Exception as e:
        print(f"❌ ERROR capturando biometría: {str(e)}")
        return None

def firma_electronica_avanzada(documento_id, datos_cliente, datos_biometricos):
    """
    Proceso completo de firma electrónica con trazabilidad
    """
    try:
        print("=== INICIANDO FIRMA ELECTRÓNICA AVANZADA ===")

        # 1. Generar hash único del documento (contrato)
        contrato = ContratoIntegracion.query.filter_by(contrato_id=documento_id).first()
        hash_contrato = hashlib.sha256(contrato.contrato_html.encode()).hexdigest()

        # 2. Obtener datos de trazabilidad
        ip_cliente = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        ubicacion = obtener_ubicacion_aprox(ip_cliente)

        # 3. Crear registro de firma
        firma_id = f"FIRMA-{documento_id}"

        firma = FirmaElectronica(
            firma_id=firma_id,
            documento_id=documento_id,
            cliente_dui=datos_cliente['dui'],
            hash_documento=hash_contrato,
            fecha_firma=datetime.now(),
            ip_cliente=ip_cliente,
            user_agent=user_agent,
            ubicacion_aprox=ubicacion,
            hash_biometrico=datos_biometricos.get('hash_facial'),
            tipo_biometria='facial',
            score_confianza=datos_biometricos.get('score_confianza', 0),
            metodo_validacion='biometria_facial',
            dispositivo_id=datos_biometricos.get('dispositivo_id')
        )

        db.session.add(firma)

        # 4. Actualizar estado del contrato
        contrato.estado = "FIRMADO"
        contrato.fecha_firma = datetime.now()

        db.session.commit()

        # 5. Generar certificado de validación
        certificado_id = generar_certificado_validacion(firma_id)

        print(f"✅ FIRMA ELECTRÓNICA REGISTRADA: {firma_id}")

        return {
            'valida': True,
            'firma_id': firma_id,
            'certificado_id': certificado_id,
            'hash_documento': hash_contrato,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ ERROR en firma electrónica: {str(e)}")
        return {'valida': False, 'error': str(e)}

def obtener_ubicacion_aprox(ip):
    """
    Obtener ubicación aproximada desde IP
    En producción, usar servicio como ipapi o similar
    """
    try:
        # Simulación - en producción integrar con API de geolocalización
        ubicaciones = {
            '127.0.0.1': 'San Salvador, El Salvador',
            '192.168.1.1': 'San Salvador, El Salvador'
        }
        return ubicaciones.get(ip, 'Ubicación no determinada')
    except:
        return 'Ubicación no disponible'

def generar_certificado_validacion(firma_id):
    """
    Generar PDF con certificado de validación y trazabilidad desde una plantilla.
    """
    try:
        firma = FirmaElectronica.query.filter_by(firma_id=firma_id).first()
        contrato = ContratoIntegracion.query.filter_by(contrato_id=firma.documento_id).first()

        certificado_id = f"CERT-{firma_id}"

        with open('backend/templates/certificado_validacion.html', 'r', encoding='utf-8') as f:
            certificado_html_template = f.read()

        certificado_html = certificado_html_template.format(
            certificado_id=certificado_id,
            documento_id=firma.documento_id,
            hash_documento=firma.hash_documento,
            fecha_firma=firma.fecha_firma.strftime('%d/%m/%Y %H:%M:%S'),
            cliente_nombre=contrato.cliente_nombre,
            cliente_dui=contrato.cliente_dui,
            cliente_email=contrato.cliente_email,
            ip_cliente=firma.ip_cliente,
            ubicacion_aprox=firma.ubicacion_aprox,
            user_agent=firma.user_agent[:100] + '...',
            timestamp_servidor=firma.timestamp_servidor.strftime('%d/%m/%Y %H:%M:%S'),
            tipo_biometria=firma.tipo_biometria,
            score_confianza=firma.score_confianza,
            metodo_validacion=firma.metodo_validacion,
            hash_biometrico=firma.hash_biometrico,
            dispositivo_id=firma.dispositivo_id,
            timestamp_sello=datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        )

        # Guardar certificado
        certificado = CertificadoValidacion(
            certificado_id=certificado_id,
            firma_id=firma_id,
            documento_id=firma.documento_id,
            cliente_dui=firma.cliente_dui,
            pdf_certificado=certificado_html,
            valido_hasta=datetime.now() + timedelta(days=365*5)  # 5 años
        )

        db.session.add(certificado)
        db.session.commit()

        print(f"✅ CERTIFICADO GENERADO: {certificado_id}")
        return certificado_id

    except Exception as e:
        print(f"❌ ERROR generando certificado: {str(e)}")
        return None