from fpdf import FPDF
from io import BytesIO
from xhtml2pdf import pisa

def convert_html_to_pdf(html_content):
    """
    Convierte un string de contenido HTML a un PDF en memoria.
    """
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(
        BytesIO(html_content.encode("UTF-8")), # El HTML de entrada
        dest=pdf_buffer,                      # El buffer de salida
        encoding='UTF-8'
    )

    if pisa_status.err:
        print(f"Error al convertir HTML a PDF: {pisa_status.err}")
        return None

    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Contrato de Préstamo - GRUPO LAZO ARCE S.A.S. DE C.V.', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_amortization_table(self, table_data):
        self.set_font('Arial', 'B', 10)
        col_widths = [15, 30, 25, 25, 25, 30, 30]
        headers = ['Mes', 'Saldo Inicial', 'Cuota', 'Interés', 'Comisión', 'Amortización', 'Saldo Final']

        for header, width in zip(headers, col_widths):
            self.cell(width, 10, header, 1, 0, 'C')
        self.ln()

        self.set_font('Arial', '', 9)
        for row in table_data:
            self.cell(col_widths[0], 10, str(row['month']), 1)
            self.cell(col_widths[1], 10, f"${row['initial_balance']:.2f}", 1)
            self.cell(col_widths[2], 10, f"${row['payment']:.2f}", 1)
            self.cell(col_widths[3], 10, f"${row['interest']:.2f}", 1)
            self.cell(col_widths[4], 10, f"${row['commission']:.2f}", 1)
            self.cell(col_widths[5], 10, f"${row['principal']:.2f}", 1)
            self.cell(col_widths[6], 10, f"${row['final_balance']:.2f}", 1)
            self.ln()
        self.ln(10)


def generate_contract_pdf(contract_data):
    pdf = PDF()
    pdf.add_page()

    client = contract_data['client']
    company = contract_data['company']
    app = contract_data['application']

    pdf.chapter_title('Partes Involucradas')
    body = (
        f"PRESTAMISTA: {company['name']} (NIT: {company['nit']})\n"
        f"PRESTATARIO: {client['full_name']} (DUI: {client['dui']}, NIT: {client['nit']})"
    )
    pdf.chapter_body(body)

    pdf.chapter_title('Términos del Préstamo')
    # The TEA is now expected in the contract_data
    tea_percentage = (contract_data.get('tea_annual', 0.0) * 100)
    body = (
        f"Monto del Préstamo: ${app['amount_requested']:.2f}\n"
        f"Tasa de Interés Anual Nominal: {(app['product']['interest_rate'] * 100):.2f}%\n"
        f"Tasa Efectiva Anual (TEA): {tea_percentage:.2f}%\n"
        f"Plazo del Préstamo: {app['term_months']} meses\n"
        f"Cuota Mensual Fija: ${app['monthly_payment']:.2f}\n"
        f"Fecha de Aprobación: {app['decision_date']}"
    )
    pdf.chapter_body(body)

    pdf.chapter_title('Tabla de Amortización')
    pdf.add_amortization_table(contract_data['amortization_table'])

    pdf.chapter_title('Firmas')
    pdf.ln(20)
    pdf.cell(0, 10, '_________________________         _________________________')
    pdf.ln(5)
    pdf.cell(0, 10, f"{company['name']}                  {client['full_name']}")

    return pdf.output(dest='S').encode('latin-1')