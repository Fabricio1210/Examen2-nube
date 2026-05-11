from fpdf import FPDF
from typing import List, Dict, Any

def generate_nota_pdf(cliente: Dict[str, Any], nota: Dict[str, Any], contenido: List[Dict[str, Any]]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    pdf.cell(0, 10, f"Nota de Venta - Folio: {nota['folio']}", ln=True)
    pdf.ln(4)

    pdf.cell(0, 8, "Cliente:", ln=True)
    pdf.cell(0, 8, f"  Razon Social: {cliente['razonSocial']}", ln=True)
    pdf.cell(0, 8, f"  Nombre Comercial: {cliente['nombreComercial']}", ln=True)
    pdf.cell(0, 8, f"  RFC: {cliente['rfc']}", ln=True)
    pdf.cell(0, 8, f"  Correo: {cliente['correoElectronico']}", ln=True)
    pdf.cell(0, 8, f"  Telefono: {cliente['telefono']}", ln=True)
    pdf.ln(4)

    pdf.cell(0, 8, "Contenido:", ln=True)
    pdf.cell(30, 8, "Cantidad",     border=1)
    pdf.cell(80, 8, "Producto",     border=1)
    pdf.cell(40, 8, "Precio Unit.", border=1)
    pdf.cell(40, 8, "Importe",      border=1)
    pdf.ln()

    for item in contenido:
        pdf.cell(30, 8, str(item["cantidad"]),             border=1)
        pdf.cell(80, 8, item["nombreProducto"],            border=1)
        pdf.cell(40, 8, f"$ {item['precioUnitario']:.2f}", border=1)
        pdf.cell(40, 8, f"$ {item['importe']:.2f}",        border=1)
        pdf.ln()

    pdf.ln(4)
    pdf.cell(0, 8, f"Total: $ {nota['total']:.2f}", ln=True)
    return pdf.output(dest="S").encode("latin-1")