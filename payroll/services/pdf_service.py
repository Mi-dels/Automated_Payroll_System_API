from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO


def generate_payslip_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("PAYSLIP", styles["Title"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(f"Employee: {data['employee']}", styles["Normal"]))
    content.append(Paragraph(f"Period: {data['period']}", styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(f"Total Hours: {data['total_hours']}", styles["Normal"]))
    content.append(Paragraph(f"Overtime Hours: {data['overtime_hours']}", styles["Normal"]))
    content.append(Paragraph(f"Late Instances: {data['late_instances']}", styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph(f"Gross Pay: {data['gross_pay']}", styles["Normal"]))
    content.append(Paragraph(f"Deductions: {data['deductions']}", styles["Normal"]))
    content.append(Paragraph(f"Net Pay: {data['net_pay']}", styles["Normal"]))

    doc.build(content)
    buffer.seek(0)

    return buffer