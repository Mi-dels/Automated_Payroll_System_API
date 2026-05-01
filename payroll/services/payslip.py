from payroll.models import Salary


def get_payslip_data(employee, period):
    salary = Salary.objects.select_related("employee", "period").get(
        employee=employee,
        period=period
    )

    return {
        "employee": salary.employee,
        "period": str(salary.period),
        "total_hours": salary.total_hours,
        "overtime_hours": salary.overtime_hours,
        "late_instances": salary.late_instances_count,
        "gross_pay": salary.gross_earnings,
        "deductions": salary.lateness_deduction,
        "net_pay": salary.net_pay,
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
            "gross_earnings": salary.gross_earnings,
            "net_pay": salary.net_pay,
            "payment_status": salary.payment_status
        })

    return results