from payroll.models import Salary


def get_payslip_data(employee, period):
    salary = Salary.objects.select_related("employee", "period").get(
        employee=employee,
        period=period
    )

    return {
        "employee_name": salary.employee.username,
        "employee_email": salary.employee.email,
        "period": str(salary.period),
        "total_hours": float(salary.total_hours or 0),
        "overtime_hours": float(salary.overtime_hours or 0),
        "late_instances": float(salary.late_instances_count or 0),
        "gross_pay": float(salary.gross_earnings or 0),
        "deductions": float(salary.lateness_deduction or 0),
        "net_pay": float(salary.net_pay or 0),
    }





def export_all_payslips(period):

    salaries = Salary.objects.filter(
        period=period
    )

    results = []

    for salary in salaries:

        results.append({
            "employee_id": salary.employee.id,
            "employee_name": salary.employee.username,
            "gross_earnings": float(salary.gross_earnings or 0),
            "net_pay": float(salary.net_pay or 0),
            "payment_status": salary.payment_status
        })

    return results