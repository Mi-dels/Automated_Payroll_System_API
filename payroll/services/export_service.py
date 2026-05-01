# from payroll.models import Salary


# def export_all_payslips(period):
#     salaries = Salary.objects.filter(period=period)

#     return [
#         {
#             "employee": s.employee.id,
#             "total_hours": s.total_hours,
#             "gross": s.gross_earnings,
#             "net": s.net_pay,
#         }
#         for s in salaries
#     ]