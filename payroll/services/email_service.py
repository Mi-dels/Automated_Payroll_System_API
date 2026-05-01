from django.core.mail import EmailMessage


def send_payslip_email(user_email, pdf_buffer):
    email = EmailMessage(
        subject="Your Monthly Payslip",
        body="Find your payslip attached.",
        to=[user_email]
    )

    email.attach(
        "payslip.pdf",
        pdf_buffer.read(),
        "application/pdf"
    )

    email.send()