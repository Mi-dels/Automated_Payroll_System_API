from django.utils import timezone

from payroll.models import Salary, PayrollPeriod


def approve_salary(salary):

    if salary.payment_status == "PAID":
        raise Exception("Salary already paid")

    salary.payment_status = "APPROVED"

    salary.save()

    return salary


def mark_salary_as_paid(salary, transaction_reference=None):

    if salary.payment_status != "APPROVED":
        raise Exception(
            "Salary must be approved before payment"
        )

    salary.payment_status = "PAID"

    salary.is_paid = True

    salary.paid_at = timezone.now()

    salary.transaction_reference = transaction_reference

    salary.save()

    return salary


def bulk_pay_period(period, transaction_prefix="BULK"):

    salaries = Salary.objects.filter(
        period=period,
        payment_status="APPROVED"
    )

    paid_count = 0

    for salary in salaries:

        reference = f"{transaction_prefix}-{salary.id}"

        mark_salary_as_paid(
            salary,
            transaction_reference=reference
        )

        paid_count += 1

    # CLOSE PERIOD
    period.is_closed = True
    period.save()

    return {
        "paid_count": paid_count,
        "period_closed": True
    }