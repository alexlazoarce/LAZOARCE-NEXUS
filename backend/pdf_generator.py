from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        # Logo - Suponiendo que 'logo.png' existe en el directorio del frontend
        # En una aplicación real, esto se manejaría de forma más robusta.
        # self.image('frontend/logo.png', 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'Contrato de Prestamo', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def create_contract_pdf(contract_data):
    """
    Genera un contrato de préstamo en formato PDF.

    Args:
        contract_data (dict): Un diccionario con los datos del contrato.

    Returns:
        bytes: El contenido del PDF generado.
    """
    pdf = PDF()
    pdf.add_page()

    # --- Información de la Empresa ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, contract_data['company']['name'], 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f"NIT: {contract_data['company']['nit']}", 0, 1)
    pdf.ln(10)

    # --- Partes del Contrato ---
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, 'PARTES DEL CONTRATO', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, f"DEUDOR: {contract_data['client']['full_name']}, con DUI: {contract_data['client']['dui']} y NIT: {contract_data['client']['nit']}.")
    pdf.multi_cell(0, 5, f"ACREEDOR: {contract_data['company']['name']}.")
    pdf.ln(10)

    # --- Detalles del Préstamo ---
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, 'DETALLES DEL PRESTAMO', 0, 1)
    pdf.set_font('Arial', '', 10)
    loan = contract_data['loan']
    pdf.cell(0, 5, f"Monto del Prestamo: ${loan['requested_amount']:.2f}", 0, 1)
    pdf.cell(0, 5, f"Plazo: {loan['requested_term']} meses", 0, 1)
    pdf.cell(0, 5, f"Tasa de Interes Mensual: {loan['interest_rate']}%", 0, 1)
    pdf.ln(10)

    # --- Tabla de Amortización ---
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, 'PLAN DE PAGOS', 0, 1)

    pdf.set_font('Arial', 'B', 8)
    col_widths = [15, 30, 30, 25, 25, 30, 30]
    headers = ['Mes', 'Vencimiento', 'Saldo Inicial', 'Interes', 'Com. Adm.', 'Amortizacion', 'Cuota']
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, 'C')
    pdf.ln()

    pdf.set_font('Arial', '', 8)
    for row in contract_data['amortization']['amortization_table']:
        pdf.cell(col_widths[0], 8, str(row['Mes']), 1, 0, 'C')
        pdf.cell(col_widths[1], 8, row['Fecha Vencimiento'], 1, 0, 'C')
        pdf.cell(col_widths[2], 8, f"${row['Saldo Inicial']:.2f}", 1, 0, 'R')
        pdf.cell(col_widths[3], 8, f"${row['Interes']:.2f}", 1, 0, 'R')
        pdf.cell(col_widths[4], 8, f"${row['Com. Adm']:.2f}", 1, 0, 'R')
        pdf.cell(col_widths[5], 8, f"${row['Amortizacion']:.2f}", 1, 0, 'R')
        pdf.cell(col_widths[6], 8, f"${row['Cuota']:.2f}", 1, 0, 'R')
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1')