from fpdf import FPDF
from io import BytesIO

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'GRUPO LAZO ARCE S.A.S. DE C.V.', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def create_contract_pdf(contract_data):
    """
    Generates a PDF contract from the provided data.

    Args:
        contract_data (dict): A dictionary containing client, loan, company, and amortization data.

    Returns:
        A BytesIO buffer containing the generated PDF.
    """
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Contrato de Préstamo Simple', 0, 1, 'C')
    pdf.ln(10)

    # Client and Loan Info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Información del Cliente y Préstamo', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f"Cliente: {contract_data['client']['name']}", 0, 1)
    pdf.cell(0, 6, f"DUI: {contract_data['client']['dui']}", 0, 1)
    pdf.cell(0, 6, f"NIT: {contract_data['client']['nit']}", 0, 1)
    pdf.cell(0, 6, f"Monto del Préstamo: {contract_data['loan']['amount_text']}", 0, 1)
    pdf.cell(0, 6, f"Plazo: {contract_data['loan']['term_months']} meses", 0, 1)
    pdf.cell(0, 6, f"Tasa de Interés Anual: {contract_data['loan']['interest_rate_annual']}", 0, 1)
    pdf.cell(0, 6, f"Cuota Mensual Fija: {contract_data['loan']['monthly_payment']}", 0, 1)
    pdf.ln(10)

    # Amortization Table Header
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Tabla de Amortización', 0, 1)
    pdf.set_font('Arial', 'B', 10)
    col_width = pdf.w / 6
    pdf.cell(col_width, 8, 'Mes', 1)
    pdf.cell(col_width, 8, 'Cuota', 1)
    pdf.cell(col_width, 8, 'Principal', 1)
    pdf.cell(col_width, 8, 'Interés', 1)
    pdf.cell(col_width, 8, 'Saldo', 1)
    pdf.ln()

    # Amortization Table Body
    pdf.set_font('Arial', '', 10)
    for row in contract_data['amortization_table']:
        pdf.cell(col_width, 8, str(row['month']), 1)
        pdf.cell(col_width, 8, f"${row['payment']:.2f}", 1)
        pdf.cell(col_width, 8, f"${row['principal']:.2f}", 1)
        pdf.cell(col_width, 8, f"${row['interest']:.2f}", 1)
        pdf.cell(col_width, 8, f"${row['balance']:.2f}", 1)
        pdf.ln()

    # Signature Section
    pdf.ln(20)
    pdf.cell(pdf.w / 2, 10, '_________________________', 0, 0, 'C')
    pdf.cell(pdf.w / 2, 10, '_________________________', 0, 1, 'C')
    pdf.cell(pdf.w / 2, 6, f"{contract_data['client']['name']}", 0, 0, 'C')
    pdf.cell(pdf.w / 2, 6, f"{contract_data['company']['name']}", 0, 1, 'C')
    pdf.cell(pdf.w / 2, 6, "(Deudor)", 0, 0, 'C')
    pdf.cell(pdf.w / 2, 6, "(Acreedor)", 0, 1, 'C')

    # Create PDF in memory
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)

    return pdf_buffer