# from django.utils import timezone

# from payroll.models import Salary, PayrollPeriod


# def approve_salary(salary):

#     if salary.payment_status == "PAID":
#         raise Exception("Salary already paid")

#     salary.payment_status = "APPROVED"

#     salary.save()

#     return salary


# def mark_salary_as_paid(salary, transaction_reference=None):

#     if salary.payment_status != "APPROVED":
#         raise Exception(
#             "Salary must be approved before payment"
#         )

#     salary.payment_status = "PAID"

#     salary.is_paid = True

#     salary.paid_at = timezone.now()

#     salary.transaction_reference = transaction_reference

#     salary.save()

#     return salary


# def bulk_pay_period(period, transaction_prefix="BULK"):

#     salaries = Salary.objects.filter(
#         period=period,
#         payment_status="APPROVED"
#     )

#     paid_count = 0

#     for salary in salaries:

#         reference = f"{transaction_prefix}-{salary.id}"

#         mark_salary_as_paid(
#             salary,
#             transaction_reference=reference
#         )

#         paid_count += 1

#     # CLOSE PERIOD
#     period.is_closed = True
#     period.save()

#     return {
#         "paid_count": paid_count,
#         "period_closed": True
#     }




from django.utils import timezone
from payroll.models import Salary, PayrollPeriod
from payroll.services.flutterwave import initiate_transfer
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