from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"shifts", views.ShiftViewSet, basename="shift")
router.register(r"workspace", views.WorkspaceViewSet, basename="workspace")

router.register(r'mark_attendance', views.AttendanceViewSet)



urlpatterns = [
    # path('/lookup/<str:employee_id>/', views.employee_lookup, name='employee-lookup'),
    path('', include(router.urls)),
]