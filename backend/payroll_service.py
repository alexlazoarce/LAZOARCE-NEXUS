from decimal import Decimal, ROUND_HALF_UP

# --- Estructura de Reglas de Nómina por País ---

COUNTRY_RULES = {
    'SV': {
        'social_security': {
            'name': 'ISSS',
            'rate': Decimal('0.03'),
            'max_contribution': Decimal('30.00') # 3% sobre un máximo de $1000
        },
        'pension': {
            'name': 'AFP',
            'rate': Decimal('0.0725')
        },
        'income_tax_brackets': [
            (Decimal('0.01'), Decimal('472.00'), Decimal('0.0'), Decimal('0.0'), Decimal('0.0')),
            (Decimal('472.01'), Decimal('895.24'), Decimal('0.10'), Decimal('17.67'), Decimal('472.00')),
            (Decimal('895.25'), Decimal('2038.10'), Decimal('0.20'), Decimal('60.00'), Decimal('895.24')),
            (Decimal('2038.11'), Decimal('999999.99'), Decimal('0.30'), Decimal('288.57'), Decimal('2038.10'))
        ]
    },
    'GT': {
        'social_security': {
            'name': 'IGSS',
            'rate': Decimal('0.0483'),
            'max_contribution': None # No hay un máximo explícito general
        },
        'pension': {
            'name': 'Montepío', # Parte del IGSS
            'rate': Decimal('0.0') # Incluido en la tasa del IGSS
        },
        'income_tax_brackets': [ # Simplificado
            (Decimal('0.01'), Decimal('30000.00') / 12, Decimal('0.05'), Decimal('0.0'), Decimal('0.0')),
            (Decimal('30000.01') / 12, Decimal('999999.99'), Decimal('0.07'), Decimal('1250.00') / 12, Decimal('30000.00') / 12)
        ]
    },
    'HN': {
        'social_security': {
            'name': 'IHSS',
            'rate': Decimal('0.025'), # Solo ramo de enfermedad y maternidad
            'max_contribution': Decimal('258.11') # Sobre un techo de L 10,324.21
        },
        'pension': {
            'name': 'RAP', # Régimen de Aportaciones Privadas
            'rate': Decimal('0.015')
        },
        'income_tax_brackets': [ # Simplificado, anual dividido entre 12
            (Decimal('0.01'), Decimal('181274.00') / 12, Decimal('0.0'), Decimal('0.0'), Decimal('0.0')),
            (Decimal('181274.01') / 12, Decimal('276373.00') / 12, Decimal('0.15'), Decimal('0.0'), Decimal('181274.00') / 12)
        ]
    }
}

def _quantize(d):
    """Redondea un Decimal a 2 decimales."""
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_payslip_details(monthly_salary, country_code='SV'):
    """
    Calcula las deducciones y el salario neto para un salario mensual dado,
    según las reglas del país especificado.
    """
    if country_code not in COUNTRY_RULES:
        raise ValueError(f"Las reglas de nómina para el país '{country_code}' no están definidas.")

    rules = COUNTRY_RULES[country_code]
    salary = Decimal(str(monthly_salary))

    # 1. Calcular deducción de seguro social
    ss_rule = rules['social_security']
    social_security_deduction = salary * ss_rule['rate']
    if ss_rule['max_contribution']:
        social_security_deduction = min(social_security_deduction, ss_rule['max_contribution'])

    # 2. Calcular deducción de pensión
    pension_rule = rules['pension']
    pension_deduction = salary * pension_rule['rate']

    # 3. Calcular base imponible para Renta
    taxable_income = salary - social_security_deduction - pension_deduction

    # 4. Calcular deducción de Renta
    renta_deduction = Decimal('0.0')
    if taxable_income > rules['income_tax_brackets'][0][0]:
        for _, upper, rate, fixed_fee, excess_over in rules['income_tax_brackets']:
            if taxable_income <= upper:
                renta_deduction = ((taxable_income - excess_over) * rate) + fixed_fee
                break

    # 5. Calcular Salario Neto
    total_deductions = social_security_deduction + pension_deduction + renta_deduction
    net_salary = salary - total_deductions

    return {
        "country_code": country_code,
        "gross_salary": float(_quantize(salary)),
        f"{ss_rule['name'].lower()}_deduction": float(_quantize(social_security_deduction)),
        f"{pension_rule['name'].lower()}_deduction": float(_quantize(pension_deduction)),
        "income_tax_deduction": float(_quantize(renta_deduction)),
        "net_salary": float(_quantize(net_salary)),
    }