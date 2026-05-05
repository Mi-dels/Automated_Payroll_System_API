# from django.shortcuts import render

# # payroll/views.py
# from rest_framework import viewsets, permissions
# from .models import User
# from .serializers import UserSerializer, EmployeePreRecordSerializer
# from payroll.permissions import IsHR
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from .models import EmployeePreRecord
# from rest_framework.permissions import (
#     IsAuthenticated
# )

# class AccessPermission(permissions.BasePermission):
#     message = 'Only HR are allowed.'

    
#     def has_object_permission(self, request, view, obj):
#         # Read permissions are allowed to any request,
#         # so we'll always allow GET, HEAD or OPTIONS requests.
#         if  request.user.is_authenticated and request.user.is_hr:
#             return True

#         # Instance must have an attribute named `owner`.
#         return obj.is_hr == request.user

# class HRMasterRecordViewSet(viewsets.ModelViewSet):
#     """
#     Only HR can access this to pre-fill employee details.
#     """
#     permission_classes = [IsAuthenticated, AccessPermission]
#     queryset = EmployeePreRecord.objects.all()
#     serializer_class = EmployeePreRecordSerializer




# class UserViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated]
#     serializer_class = UserSerializer
    
#     def get_queryset(self):
#         user = self.request.user
#         if not user.is_authenticated:
#             return User.objects.none()
        
#         if user.is_hr:
#             return User.objects.all()  # HR sees the whole list
#         return User.objects.filter(id=user.id) # Employees see only their own data




# class IsHRorSelf(permissions.BasePermission):
#     """
#     Custom permission: 
#     - HR can do anything.
#     - Regular users can only see/edit themselves.
#     """
#     def has_object_permission(self, request, view, obj):
#         # Allow if the user is HR
#         if request.user.is_authenticated and request.user.is_hr:
#             return True
#         # Allow if the user is looking at their own profile
#         return obj == request.user
    

# from django.http import FileResponse

# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response

# from payroll.serializers import HRPayrollActionSerializer

# from payroll.services.payslip import get_payslip_data
# from payroll.services.pdf_service import generate_payslip_pdf
# from payroll.services.email_service import send_payslip_email



# from payroll.models import Salary, PayrollPeriod



# class EmployeePayrollViewSet(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated]
#     # =========================
#     # MY SALARY
#     # =========================
#     @action(detail=False, methods=["get"])
#     def salary(self, request):

#         user = request.user

#         month = request.query_params.get("month")
#         year = request.query_params.get("year")

#         salaries = Salary.objects.filter(employee=user)

#         if month and year:
#             salaries = salaries.filter(
#                 period__month__month=month,
#                 period__month__year=year
#             )

#         return Response({
#             "results": [
#                 {
#                     "period": str(s.period),
#                     "net_pay": s.net_pay,
#                     "status": s.payment_status
#                 }
#                 for s in salaries
#             ]
#         })


#     # =========================
#     # MY PAYSLIP (PDF)
#     # =========================
#     @action(detail=False, methods=["get"])
#     def payslip(self, request):

#         user = request.user

#         period_id = request.query_params.get("period")

#         if not period_id:
#             return Response(
#                 {"error": "period is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             period = PayrollPeriod.objects.get(id=period_id)

#             data = get_payslip_data(user, period)

#             pdf = generate_payslip_pdf(data)

#             return Response({
#                 "message": "Payslip generated",
#                 "data": data
#             })

#         except PayrollPeriod.DoesNotExist:
#             return Response(
#                 {"error": "Invalid period"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )







# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response

# from django.http import FileResponse

# from payroll.models import Salary, PayrollPeriod
# from payroll.services.payroll import generate_salary
# from payroll.services.payment import (
#     approve_salary,
#     mark_salary_as_paid,
#     bulk_pay_period
# )
# from payroll.services.payslip import (
#     get_payslip_data,
    
#     # send_payslip_email,
#     export_all_payslips
# )


# class HRPayrollsViewSet(viewsets.ViewSet):
#     permission_classes = [
#         IsAuthenticated,
#         IsHR
#     ]
#     # =========================
#     # GENERATE SALARY
#     # =========================
#     @action(detail=False, methods=["post"])
#     def generate(self, request):

#         user_id = request.data.get("employee_id")
#         year = request.data.get("year")
#         month = request.data.get("month")

#         period = PayrollPeriod.objects.filter(
#             month__year=year,
#             month__month=month
#         ).first()

#         if not period:
#             return Response(
#                 {"error": "Payroll period not found"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         from django.contrib.auth import get_user_model
#         User = get_user_model()

#         user = User.objects.get(id=user_id)

#         result = generate_salary(user, year, month)

#         return Response(result)


#     # =========================
#     # APPROVE SALARY
#     # =========================
#     @action(detail=False, methods=["post"])
#     def approve(self, request):

#         salary_id = request.data.get("salary_id")

#         salary = Salary.objects.get(id=salary_id)

#         approve_salary(salary)

#         return Response({"message": "Salary approved"})


#     # =========================
#     # PAY SALARY
#     # =========================
#     @action(detail=False, methods=["post"])
#     def pay(self, request):

#         salary_id = request.data.get("salary_id")
#         reference = request.data.get("reference")

#         salary = Salary.objects.get(id=salary_id)

#         mark_salary_as_paid(salary, reference)

#         return Response({"message": "Payment successful"})


#     # =========================
#     # BULK PAY
#     # =========================
#     @action(detail=False, methods=["post"])
#     def bulk_pay(self, request):

#         period_id = request.data.get("period_id")

#         period = PayrollPeriod.objects.get(id=period_id)

#         result = bulk_pay_period(period)

#         return Response(result)


#     # =========================
#     # EXPORT PAYSLIPS
#     # =========================
#     @action(detail=False, methods=["get"])
#     def export(self, request):

#         period_id = request.query_params.get("period_id")

#         period = PayrollPeriod.objects.get(id=period_id)

#         result = export_all_payslips(period)

#         return Response(result)







from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .models import User, EmployeePreRecord, Salary, PayrollPeriod
from .serializers import (
    UserSerializer,
    EmployeePreRecordSerializer,
    HRPayrollActionSerializer,
    SalaryApprovalSerializer,
    SalaryPaymentSerializer,
    BulkPaymentSerializer,
)
from payroll.permissions import IsHR
from payroll.services.payroll import generate_salary
from payroll.services.payment import approve_salary, mark_salary_as_paid, bulk_pay_period
from payroll.services.payslip import get_payslip_data, export_all_payslips
from payroll.services.pdf_service import generate_payslip_pdf

class AccessPermission(permissions.BasePermission):
    message = 'Only HR are allowed.'

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and request.user.is_hr:
            return True
        return obj.is_hr == request.user

class HRMasterRecordViewSet(viewsets.ModelViewSet):
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
            return User.objects.all()
        return User.objects.filter(id=user.id)

class IsHRorSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and request.user.is_hr:
            return True
        return obj == request.user

class EmployeePayrollViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

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

class HRPayrollsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsHR]

    @extend_schema(request=HRPayrollActionSerializer)
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

    @extend_schema(request=SalaryApprovalSerializer)
    @action(detail=False, methods=["post"])
    def approve(self, request):
        salary_id = request.data.get("salary_id")
        salary = Salary.objects.get(id=salary_id)
        approve_salary(salary)
        return Response({"message": "Salary approved"})

    @extend_schema(request=SalaryPaymentSerializer)
    @action(detail=False, methods=["post"])
    def pay(self, request):
        salary_id = request.data.get("salary_id")
        reference = request.data.get("reference")
        salary = Salary.objects.get(id=salary_id)
        mark_salary_as_paid(salary, reference)
        return Response({"message": "Payment successful"})

    @extend_schema(request=BulkPaymentSerializer)
    @action(detail=False, methods=["post"])
    def bulk_pay(self, request):
        period_id = request.data.get("period_id")
        period = PayrollPeriod.objects.get(id=period_id)
        result = bulk_pay_period(period)
        return Response(result)

    @action(detail=False, methods=["get"])
    def export(self, request):
        period_id = request.query_params.get("period_id")
        period = PayrollPeriod.objects.get(id=period_id)
        result = export_all_payslips(period)
        return Response(result)



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import hmac
import hashlib
from django.conf import settings

@extend_schema(exclude=True)
@api_view(["POST"])
@permission_classes([AllowAny])
def flutterwave_webhook(request):
    secret_hash = settings.FLUTTERWAVE_SECRET_HASH
    signature = request.headers.get("verif-hash")

    if not signature or not hmac.compare_digest(
        hashlib.sha256(secret_hash.encode()).hexdigest(),
        hashlib.sha256(signature.encode()).hexdigest()
    ):
        return Response({"error": "Invalid signature"}, status=status.HTTP_401_UNAUTHORIZED)

    payload = request.data
    event = payload.get("event")

    if event == "transfer.completed":
        reference = payload["data"]["reference"]
        transfer_status = payload["data"]["status"]

        try:
            salary = Salary.objects.get(transaction_reference=reference)
            if transfer_status == "SUCCESSFUL":
                salary.payment_status = "PAID"
                salary.is_paid = True
                salary.paid_at = timezone.now()
                salary.save()
            elif transfer_status == "FAILED":
                salary.payment_status = "APPROVED"
                salary.is_paid = False
                salary.save()
        except Salary.DoesNotExist:
            pass

    return Response({"status": "ok"}, status=status.HTTP_200_OK)




# @extend_schema(exclude=True)
# @api_view(["POST"])
# @permission_classes([AllowAny])
# def flutterwave_webhook(request):
#     secret_hash = settings.FLUTTERWAVE_SECRET_HASH
#     signature = request.headers.get("verif-hash")

#     if signature != secret_hash:
#         return Response({"error": "Invalid signature"}, status=status.HTTP_401_UNAUTHORIZED)

#     payload = request.data
#     event = payload.get("event")

#     if event == "transfer.completed":
#         reference = payload["data"]["reference"]
#         transfer_status = payload["data"]["status"]

#         try:
#             salary = Salary.objects.get(transaction_reference=reference)
#             if transfer_status == "SUCCESSFUL":
#                 salary.payment_status = "PAID"
#                 salary.is_paid = True
#                 salary.paid_at = timezone.now()
#                 salary.save()
#             elif transfer_status == "FAILED":
#                 salary.payment_status = "APPROVED"
#                 salary.is_paid = False
#                 salary.save()
#         except Salary.DoesNotExist:
#             pass

#     return Response({"status": "ok"}, status=status.HTTP_200_OK)









