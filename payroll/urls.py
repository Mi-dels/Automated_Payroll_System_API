from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from payroll.views import flutterwave_webhook
# payroll/urls.py




# The router automatically creates the routes for 'users/'
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'hr-pre-records', views.HRMasterRecordViewSet)
router.register(r'hr/payroll', views.HRPayrollsViewSet, basename='hr-payroll')
router.register(r'employee/payroll', views.EmployeePayrollViewSet, basename='employee-payroll')
router.register(r'payroll_periods', views.PayrollPeriodViewSet, basename='payroll_period')
router.register(r'payroll_config', views.PayrollConfigurationViewSet, basename='payroll_config')

urlpatterns = [
    # path('/lookup/<str:employee_id>/', views.employee_lookup, name='employee-lookup'),
    path('', include(router.urls)),
    path('flutterwave/webhook/', flutterwave_webhook, name='flutterwave_webhook')
]


