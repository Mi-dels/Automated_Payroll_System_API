from django.shortcuts import render

# payroll/views.py
from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserSerializer, EmployeePreRecordSerializer
from payroll.permissions import IsHR
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import EmployeePreRecord
from rest_framework.permissions import (
    IsAuthenticated
)

class AccessPermission(permissions.BasePermission):
    message = 'Only HR are allowed.'

    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if  request.user.is_authenticated and request.user.is_hr:
            return True

        # Instance must have an attribute named `owner`.
        return obj.is_hr == request.user

class HRMasterRecordViewSet(viewsets.ModelViewSet):
    """
    Only HR can access this to pre-fill employee details.
    """
    permission_classes = [IsAuthenticated, AccessPermission]
    queryset = EmployeePreRecord.objects.all()
    serializer_class = EmployeePreRecordSerializer




class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        
        if user.is_hr:
            return User.objects.all()  # HR sees the whole list
        return User.objects.filter(id=user.id) # Employees see only their own data




class IsHRorSelf(permissions.BasePermission):
    """
    Custom permission: 
    - HR can do anything.
    - Regular users can only see/edit themselves.
    """
    def has_object_permission(self, request, view, obj):
        # Allow if the user is HR
        if request.user.is_authenticated and request.user.is_hr:
            return True
        # Allow if the user is looking at their own profile
        return obj == request.user
    

from django.http import FileResponse

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from payroll.serializers import HRPayrollActionSerializer

from payroll.services.payslip import get_payslip_data
from payroll.services.pdf_service import generate_payslip_pdf
from payroll.services.email_service import send_payslip_email



from payroll.models import Salary, PayrollPeriod



class EmployeePayrollViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    # =========================
    # MY SALARY
    # =========================
    @action(detail=False, methods=["get"])
    def salary(self, request):

        user = request.user

        month = request.query_params.get("month")
        year = request.query_params.get("year")

        salaries = Salary.objects.filter(employee=user)

        if month and year:
            salaries = salaries.filter(
                period__month__month=month,
                period__month__year=year
            )

        return Response({
            "results": [
                {
                    "period": str(s.period),
                    "net_pay": s.net_pay,
                    "status": s.payment_status
                }
                for s in salaries
            ]
        })


    # =========================
    # MY PAYSLIP (PDF)
    # =========================
    @action(detail=False, methods=["get"])
    def payslip(self, request):

        user = request.user

        period_id = request.query_params.get("period")

        if not period_id:
            return Response(
                {"error": "period is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            period = PayrollPeriod.objects.get(id=period_id)

            data = get_payslip_data(user, period)

            pdf = generate_payslip_pdf(data)

            return Response({
                "message": "Payslip generated",
                "data": data
            })

        except PayrollPeriod.DoesNotExist:
            return Response(
                {"error": "Invalid period"},
                status=status.HTTP_400_BAD_REQUEST
            )



# # =========================================================
# # EMPLOYEE PAYROLL PORTAL
# # =========================================================
# class EmployeePayrollViewSet(viewsets.ViewSet):

#     @action(detail=False, methods=["get"])
#     def payslip(self, request):

#         user = request.user

#         period_id = request.query_params.get("period")

#         if not period_id:
#             return Response(
#                 {"error": "period query parameter is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             period = PayrollPeriod.objects.get(id=period_id)

#         except PayrollPeriod.DoesNotExist:
#             return Response(
#                 {"error": "Invalid payroll period"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             data = get_payslip_data(user, period)

#             pdf = generate_payslip_pdf(data)

#             return FileResponse(
#                 pdf,
#                 as_attachment=True,
#                 filename=f"payslip_{user.id}_{period.month}.pdf"
#             )

#         except Exception as e:
#             return Response(
#                 {"error": str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#     # OPTIONAL
#     @action(detail=False, methods=["get"])
#     def salary_history(self, request):

#         user = request.user

#         history = []

#         for salary in user.salaries.all().order_by("-created_at"):

#             history.append({
#                 "period": str(salary.period),
#                 "gross_earnings": salary.gross_earnings,
#                 "net_pay": salary.net_pay,
#                 "payment_status": salary.payment_status,
#                 "is_paid": salary.is_paid
#             })

#         return Response(history)



# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response

# from django.http import FileResponse
# from django.contrib.auth import get_user_model

# from payroll.models import Salary, PayrollPeriod

# from payroll.serializers import (
#     HRPayrollActionSerializer,
#     SalaryApprovalSerializer,
#     SalaryPaymentSerializer,
#     BulkPaymentSerializer
# )

# from payroll.services.payroll import generate_salary

# from payroll.services.payslip import (
#     get_payslip_data,
#     export_all_payslips
# )

# from payroll.services.pdf_service import (
#     generate_payslip_pdf
# )

# from payroll.services.email_service import (
#     send_payslip_email
# )

# from payroll.services.payment import (
#     approve_salary,
#     mark_salary_as_paid,
#     bulk_pay_period
# )

# from payroll.permissions import require_hr



# User = get_user_model()



from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.http import FileResponse

from payroll.models import Salary, PayrollPeriod
from payroll.services.payroll import generate_salary
from payroll.services.payment import (
    approve_salary,
    mark_salary_as_paid,
    bulk_pay_period
)
from payroll.services.payslip import (
    get_payslip_data,
    
    # send_payslip_email,
    export_all_payslips
)


class HRPayrollsViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        IsHR
    ]
    # =========================
    # GENERATE SALARY
    # =========================
    @action(detail=False, methods=["post"])
    def generate(self, request):

        user_id = request.data.get("employee_id")
        year = request.data.get("year")
        month = request.data.get("month")

        period = PayrollPeriod.objects.filter(
            month__year=year,
            month__month=month
        ).first()

        if not period:
            return Response(
                {"error": "Payroll period not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.get(id=user_id)

        result = generate_salary(user, year, month)

        return Response(result)


    # =========================
    # APPROVE SALARY
    # =========================
    @action(detail=False, methods=["post"])
    def approve(self, request):

        salary_id = request.data.get("salary_id")

        salary = Salary.objects.get(id=salary_id)

        approve_salary(salary)

        return Response({"message": "Salary approved"})


    # =========================
    # PAY SALARY
    # =========================
    @action(detail=False, methods=["post"])
    def pay(self, request):

        salary_id = request.data.get("salary_id")
        reference = request.data.get("reference")

        salary = Salary.objects.get(id=salary_id)

        mark_salary_as_paid(salary, reference)

        return Response({"message": "Payment successful"})


    # =========================
    # BULK PAY
    # =========================
    @action(detail=False, methods=["post"])
    def bulk_pay(self, request):

        period_id = request.data.get("period_id")

        period = PayrollPeriod.objects.get(id=period_id)

        result = bulk_pay_period(period)

        return Response(result)


    # =========================
    # EXPORT PAYSLIPS
    # =========================
    @action(detail=False, methods=["get"])
    def export(self, request):

        period_id = request.query_params.get("period_id")

        period = PayrollPeriod.objects.get(id=period_id)

        result = export_all_payslips(period)

        return Response(result)





















# # =========================================================
# # HR PAYROLL PORTAL
# # =========================================================
# class HRPayrollsViewSet(viewsets.ViewSet):

#     permission_classes = [AccessPermission]

#     # =====================================================
#     # RUN MONTHLY PAYROLL
#     # =====================================================
#     @action(detail=False, methods=["post"])
#     def run_month(self, request):

#         month = request.data.get("month")

#         if not month:
#             return Response(
#                 {"error": "month is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             period = PayrollPeriod.objects.get(month=month)

#         except PayrollPeriod.DoesNotExist:
#             return Response(
#                 {"error": "Payroll period not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         employees = User.objects.all()

#         results = []
#         failed = 0

#         for user in employees:

#             try:
#                 salary_data = generate_salary(
#                     user,
#                     period.month.year,
#                     period.month.month
#                 )

#                 results.append({
#                     "employee_id": user.id,
#                     "status": "success",
#                     "data": salary_data
#                 })

#             except Exception as e:

#                 failed += 1

#                 results.append({
#                     "employee_id": user.id,
#                     "status": "failed",
#                     "error": str(e)
#                 })

#         return Response({
#             "message": "Payroll run completed",
#             "total_employees": employees.count(),
#             "successful": employees.count() - failed,
#             "failed": failed,
#             "results": results
#         })

#     # =====================================================
#     # GENERATE PAYSLIP / EMAIL / EXPORT
#     # =====================================================
#     def create(self, request):

#         require_hr(request.user)

#         serializer = HRPayrollActionSerializer(
#             data=request.data
#         )

#         serializer.is_valid(raise_exception=True)

#         action_name = serializer.validated_data["action"]

#         employee = serializer.validated_data.get(
#             "employee"
#         )

#         period = serializer.validated_data["period"]

#         format_type = serializer.validated_data["format"]

#         # =================================================
#         # GENERATE PAYSLIP
#         # =================================================
#         if action_name == "generate_payslip":

#             try:

#                 data = get_payslip_data(
#                     employee,
#                     period
#                 )

#                 if format_type == "pdf":

#                     pdf = generate_payslip_pdf(data)

#                     return FileResponse(
#                         pdf,
#                         as_attachment=True,
#                         filename=f"payslip_{employee.id}_{period.month}.pdf"
#                     )

#                 return Response(data)

#             except Exception as e:

#                 return Response(
#                     {"error": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # =================================================
#         # SEND EMAIL
#         # =================================================
#         if action_name == "send_email":

#             try:

#                 data = get_payslip_data(
#                     employee,
#                     period
#                 )

#                 pdf = generate_payslip_pdf(data)

#                 send_payslip_email(
#                     user_email=employee.email,
#                     pdf_buffer=pdf
#                 )

#                 return Response({
#                     "message": "Payslip email sent successfully"
#                 })

#             except Exception as e:

#                 return Response(
#                     {"error": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # =================================================
#         # BULK EXPORT
#         # =================================================
#         if action_name == "bulk_export":

#             try:

#                 result = export_all_payslips(period)

#                 return Response({
#                     "message": "Bulk export completed",
#                     "data": result
#                 })

#             except Exception as e:

#                 return Response(
#                     {"error": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         return Response(
#             {"error": "Invalid payroll action"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     # =====================================================
#     # APPROVE SALARY
#     # =====================================================
#     @action(detail=False, methods=["post"])
#     def approve_salary(self, request):

#         require_hr(request.user)

#         serializer = SalaryApprovalSerializer(
#             data=request.data
#         )

#         serializer.is_valid(raise_exception=True)

#         salary_id = serializer.validated_data["salary_id"]

#         try:

#             salary = Salary.objects.get(id=salary_id)

#             approve_salary(salary)

#             return Response({
#                 "message": "Salary approved successfully"
#             })

#         except Salary.DoesNotExist:

#             return Response(
#                 {"error": "Salary not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         except Exception as e:

#             return Response(
#                 {"error": str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#     # =====================================================
#     # PAY SINGLE SALARY
#     # =====================================================
#     @action(detail=False, methods=["post"])
#     def pay_salary(self, request):

        
#         require_hr(request.user)

#         serializer = SalaryPaymentSerializer(
#             data=request.data
#         )

#         serializer.is_valid(raise_exception=True)

#         salary_id = serializer.validated_data["salary_id"]

#         transaction_reference = serializer.validated_data.get(
#             "transaction_reference"
#         )

#         try:

#             salary = Salary.objects.get(id=salary_id)

#             mark_salary_as_paid(
#                 salary,
#                 transaction_reference
#             )

#             return Response({
#                 "message": "Salary paid successfully"
#             })

#         except Salary.DoesNotExist:

#             return Response(
#                 {"error": "Salary not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         except Exception as e:

#             return Response(
#                 {"error": str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#     # =====================================================
#     # BULK PAYMENT
#     # =====================================================
#     @action(detail=False, methods=["post"])
#     def bulk_pay(self, request):

#         require_hr(request.user)

#         serializer = BulkPaymentSerializer(
#             data=request.data
#         )

#         serializer.is_valid(raise_exception=True)

#         period_id = serializer.validated_data["period_id"]

#         transaction_prefix = serializer.validated_data[
#             "transaction_prefix"
#         ]

#         try:

#             period = PayrollPeriod.objects.get(
#                 id=period_id
#             )

#             result = bulk_pay_period(
#                 period,
#                 transaction_prefix
#             )

#             return Response({
#                 "message": "Bulk payment completed",
#                 "data": result
#             })

#         except PayrollPeriod.DoesNotExist:

#             return Response(
#                 {"error": "Payroll period not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         except Exception as e:

#             return Response(
#                 {"error": str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )





# =========================================================
# HR PAYROLL PORTAL  -  NEW ONE
# =========================================================
# class HRPayrollsViewSet(viewsets.ViewSet):

#     def create(self, request):

#         serializer = HRPayrollActionSerializer(data=request.data)

#         serializer.is_valid(raise_exception=True)

#         action_name = serializer.validated_data["action"]

#         employee = serializer.validated_data.get("employee")

#         period = serializer.validated_data["period"]

#         format_type = serializer.validated_data["format"]

#         # =================================================
#         # GENERATE PAYSLIP
#         # =================================================
#         if action_name == "generate_payslip":

#             try:
#                 data = get_payslip_data(employee, period)

#                 # PDF RESPONSE
#                 if format_type == "pdf":

#                     pdf = generate_payslip_pdf(data)

#                     return FileResponse(
#                         pdf,
#                         as_attachment=True,
#                         filename=f"payslip_{employee.id}_{period.month}.pdf"
#                     )

#                 # JSON RESPONSE
#                 return Response(data)

#             except Exception as e:
#                 return Response(
#                     {"error": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # =================================================
#         # SEND EMAIL PAYSLIP
#         # =================================================
#         if action_name == "send_email":

#             try:
#                 data = get_payslip_data(employee, period)

#                 pdf = generate_payslip_pdf(data)

#                 send_payslip_email(
#                     user_email=employee.email,
#                     pdf_buffer=pdf
#                 )

#                 return Response(
#                     {"message": "Payslip email sent successfully"},
#                     status=status.HTTP_200_OK
#                 )

#             except Exception as e:
#                 return Response(
#                     {"error": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # =================================================
#         # BULK EXPORT
#         # =================================================
#         if action_name == "bulk_export":

#             try:
#                 result = export_all_payslips(period)

#                 return Response(
#                     {
#                         "message": "Bulk export completed",
#                         "data": result
#                     },
#                     status=status.HTTP_200_OK
#                 )

#             except Exception as e:
#                 return Response(
#                     {"error": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         return Response(
#             {"error": "Invalid payroll action"},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    

#     @action(detail=False, methods=["post"])
# def approve_salary(self, request):

#     serializer = SalaryApprovalSerializer(
#         data=request.data
#     )

#     serializer.is_valid(raise_exception=True)

#     salary_id = serializer.validated_data["salary_id"]

#     try:
#         salary = Salary.objects.get(id=salary_id)

#         approve_salary(salary)

#         return Response({
#             "message": "Salary approved successfully"
#         })

#     except Salary.DoesNotExist:
#         return Response(
#             {"error": "Salary not found"},
#             status=status.HTTP_404_NOT_FOUND
#         )

#     except Exception as e:
#         return Response(
#             {"error": str(e)},
#             status=status.HTTP_400_BAD_REQUEST
#         )



# # =========================================================
# # HR PAYROLL PORTAL -  OLD ONE
# # =========================================================
# class HRPayrollViewSet(viewsets.ViewSet):

#     def create(self, request):

#         serializer = HRPayrollActionSerializer(data=request.data)

#         serializer.is_valid(raise_exception=True)

#         action_name = serializer.validated_data["action"]

#         employee = serializer.validated_data.get("employee")

#         period = serializer.validated_data["period"]

#         format_type = serializer.validated_data["format"]

#         # =================================================
#         # GENERATE PAYSLIP
#         # =================================================
#         if action_name == "generate_payslip":

#             try:
#                 data = get_payslip_data(employee, period)

#                 # PDF RESPONSE
#                 if format_type == "pdf":

#                     pdf = generate_payslip_pdf(data)

#                     return FileResponse(
#                         pdf,
#                         as_attachment=True,
#                         filename=f"payslip_{employee.id}_{period.month}.pdf"
#                     )

#                 # JSON RESPONSE
#                 return Response(data)

#             except Exception as e:
#                 return Response(
#                     {"error": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # =================================================
#         # SEND EMAIL PAYSLIP
#         # =================================================
#         if action_name == "send_email":

#             try:
#                 data = get_payslip_data(employee, period)

#                 pdf = generate_payslip_pdf(data)

#                 send_payslip_email(
#                     user_email=employee.email,
#                     pdf_buffer=pdf
#                 )

#                 return Response(
#                     {"message": "Payslip email sent successfully"},
#                     status=status.HTTP_200_OK
#                 )

#             except Exception as e:
#                 return Response(
#                     {"error": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # =================================================
#         # BULK EXPORT
#         # =================================================
#         if action_name == "bulk_export":

#             try:
#                 result = export_all_payslips(period)

#                 return Response(
#                     {
#                         "message": "Bulk export completed",
#                         "data": result
#                     },
#                     status=status.HTTP_200_OK
#                 )

#             except Exception as e:
#                 return Response(
#                     {"error": str(e)},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         return Response(
#             {"error": "Invalid payroll action"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = [IsHRorSelf]

#     def get_queryset(self):
#         # This is the "Self-only" filter for the LIST view
#         user = self.request.user
#         if user.is_authenticated:
#             if user.is_hr:
#                 return User.objects.all() # HR sees everyone
#             return User.objects.filter(id=user.id) # Employees see only themselves
#         return User.objects.none() # Unauthenticated users see nothing

# @api_view(['GET'])
# def employee_lookup(request, employee_id):
#     try:
#         record = EmployeePreRecord.objects.get(employee_id=employee_id)
#         return Response({
#             'department': record.department.id,
#             'job_title': record.job_title.id,
#             'employment_status': record.employment_status.id,
#             'is_hr': record.is_hr,
#         })
#     except EmployeePreRecord.DoesNotExist:
#         return Response({'error': 'Not found'}, status=404)
    #  def get_permissions(self):
    #     # Strictly restrict this whole API to HR only
    #     if self.request.user.is_authenticated and self.request.user.is_hr:
    #         return [permissions.IsAuthenticated()]
    #     return [permissions.]

