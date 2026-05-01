from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
# payroll/urls.py




# The router automatically creates the routes for 'users/'
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'hr-pre-records', views.HRMasterRecordViewSet)
router.register(r'hr/payroll', views.HRPayrollsViewSet, basename='hr-payroll')
router.register(r'employee/payroll', views.EmployeePayrollViewSet, basename='employee-payroll')

urlpatterns = [
    # path('/lookup/<str:employee_id>/', views.employee_lookup, name='employee-lookup'),
    path('', include(router.urls)),
]


