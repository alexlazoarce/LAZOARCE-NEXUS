from decimal import Decimal, ROUND_HALF_UP

# --- Estructura de Reglas de Nómina por País (Avanzada) ---

COUNTRY_RULES = {
    'SV': {
        'social_security': {
            'name': 'ISSS',
            'rate': Decimal('0.03'),
            'max_contribution_amount': Decimal('30.00') # Esto corresponde al 3% de $1000.00
        },
        'pension': {
            'name': 'AFP',
            'rate': Decimal('0.0725'),
            'max_taxable_salary': Decimal('7045.06') # Techo de AFP
        },
        'income_tax_brackets': [
            # (Límite Inferior, Límite Superior, Tasa, Cuota Fija, Exceso Sobre)
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
            'max_taxable_salary': None # Sin límite en Guatemala
        },
        'pension': { 'name': 'Montepío', 'rate': Decimal('0.0') },
        'income_tax_brackets': [ # Simplificado
            (Decimal('0.01'), Decimal('30000.00') / 12, Decimal('0.05'), Decimal('0.0'), Decimal('0.0')),
            (Decimal('30000.01') / 12, Decimal('999999.99'), Decimal('0.07'), Decimal('1250.00') / 12, Decimal('30000.00') / 12)
        ]
    },
    # ... (Otros países se mantienen como en la versión avanzada)
}

def _quantize(d):
    """Redondea un Decimal a 2 decimales para consistencia."""
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_payslip_details(monthly_salary, country_code='SV'):
    """
    Calcula las deducciones y el salario neto para un salario mensual dado,
    según las reglas del país especificado (default: SV - El Salvador).
    """
    if country_code not in COUNTRY_RULES:
        return {"success": False, "error": f"Las reglas de nómina para el país '{country_code}' no están definidas."}

    rules = COUNTRY_RULES[country_code]
    salary = Decimal(str(monthly_salary))

    try:
        # 1. Calcular deducción de seguro social (ISSS, IGSS, etc.)
        ss_rule = rules['social_security']
        
        # Determinar el salario gravable para SS
        ss_taxable_salary = salary
        
        # Si el país tiene un límite de contribución (ej. SV: $30.00), aplicarlo.
        social_security_deduction = salary * ss_rule.get('rate', Decimal('0.0'))
        if 'max_contribution_amount' in ss_rule and ss_rule['max_contribution_amount'] is not None:
             social_security_deduction = min(social_security_deduction, ss_rule['max_contribution_amount'])
        # Nota: La lógica del HEAD ($1000.00 * 3%) se cumple con el 'max_contribution_amount' de $30.00

        # 2. Calcular deducción de pensión (AFP, RAP, etc.)
        pension_rule = rules['pension']
        
        # Determinar el salario gravable para Pensión (ej. SV: $7045.06)
        pension_taxable_salary = salary
        if 'max_taxable_salary' in pension_rule and pension_rule['max_taxable_salary'] is not None:
             pension_taxable_salary = min(salary, pension_rule['max_taxable_salary'])
        
        pension_deduction = pension_taxable_salary * pension_rule.get('rate', Decimal('0.0'))

        # 3. Calcular base imponible para Renta
        taxable_income = salary - social_security_deduction - pension_deduction

        # 4. Calcular deducción de Renta
        renta_deduction = Decimal('0.0')
        if rules.get('income_tax_brackets'):
            
            # Buscar el tramo correspondiente
            found_bracket = False
            for lower, upper, rate, fixed_fee, excess_over in rules['income_tax_brackets']:
                if lower <= taxable_income <= upper:
                    # Aplicar la fórmula
                    exceso = taxable_income - excess_over
                    renta_deduction = (exceso * rate) + fixed_fee
                    found_bracket = True
                    break
            
            if not found_bracket and taxable_income > rules['income_tax_brackets'][-1][1]:
                 # Caso para el tramo más alto
                 lower, upper, rate, fixed_fee, excess_over = rules['income_tax_brackets'][-1]
                 exceso = taxable_income - excess_over
                 renta_deduction = (exceso * rate) + fixed_fee

        # 5. Calcular Salario Neto
        total_deductions = social_security_deduction + pension_deduction + renta_deduction
        net_salary = salary - total_deductions

        # 6. Formatear la respuesta (similar al HEAD pero usando las variables del 2.0)
        return {
            "success": True,
            "salario_base": float(_quantize(salary)),
            "social_security_name": ss_rule['name'],
            "social_security_deduction": float(_quantize(social_security_deduction)),
            "pension_name": pension_rule['name'],
            "pension_deduction": float(_quantize(pension_deduction)),
            "income_tax_deduction": float(_quantize(renta_deduction)),
            "total_deducciones": float(_quantize(total_deductions)),
            "salario_neto": float(_quantize(net_salary)),
        }
        
    except Exception as e:
        # Se captura cualquier error inesperado y se devuelve en el formato del HEAD
        return {"success": False, "error": str(e)}

# Para mantener la compatibilidad con llamadas externas que usan el nombre del HEAD
calcular_planilla = calculate_payslip_details