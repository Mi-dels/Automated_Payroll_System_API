from django.utils import timezone
from payroll.models import Salary, PayrollPeriod
from payroll.services.flutterwave import initiate_transfer
from payroll.services.payslip import get_payslip_data
from payroll.services.pdf_service import generate_payslip_pdf
from payroll.services.email_service import send_payslip_email
import uuid


def approve_salary(salary):
    if salary.payment_status == "PAID":
        raise Exception("Salary already paid")
    salary.payment_status = "APPROVED"
    salary.save()
    return salary


def mark_salary_as_paid(salary, transaction_reference=None):
    if salary.payment_status != "APPROVED":
        raise Exception("Salary must be approved before payment")

    employee = salary.employee

    if not employee.bank_account_number or not employee.bank_code:
        raise Exception(f"Employee {employee.username} has no bank details on file")

    reference = transaction_reference or f"PAYROLL-{salary.id}-{uuid.uuid4().hex[:8].upper()}"

    result = initiate_transfer(
        amount=salary.net_pay,
        account_number=employee.bank_account_number,
        bank_code=employee.bank_code,
        account_name=getattr(employee, 'full_name', None) or employee.username,
        reference=reference,
        narration=f"Salary payment for {salary.period}",
    )

    salary.payment_status = "PAID"
    salary.is_paid = True
    salary.paid_at = timezone.now()
    salary.transaction_reference = result["reference"]
    salary.save()


    try:
        period = salary.period
        payslip_data = get_payslip_data(employee, period)
        pdf = generate_payslip_pdf(payslip_data)
        send_payslip_email(
            user_email=employee.email,
            pdf_buffer=pdf
        )

    except Exception as e:
        print(f"Email sending failed for {employee.username}: {str(e)}")

    return salary


def bulk_pay_period(period):
    salaries = Salary.objects.filter(
        period=period,
        payment_status="APPROVED"
    )

    paid_count = 0
    failed = []

    for salary in salaries:
        try:
            mark_salary_as_paid(salary)
            paid_count += 1
        except Exception as e:
            failed.append({
                "employee": salary.employee.username,
                "error": str(e)
            })

    period.is_closed = True
    period.save()

    return {
        "paid_count": paid_count,
        "failed_count": len(failed),
        "failed": failed,
        "period_closed": True
    }