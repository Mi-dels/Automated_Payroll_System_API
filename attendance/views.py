from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.gis.geos import Point
from drf_spectacular.utils import extend_schema

from attendance.models import Attendance, Workspace, Shift
from attendance.serializers import (
    AttendanceSerializer,
    ClockInSerializer,
    ClockOutSerializer,
    WorkspaceSerializer,
    ShiftSerializer,
    EmergencyClockOutSerializer
)
from attendance.services.clock_in import process_clock_in
from attendance.services.clock_out import process_clock_out, process_emergency_clock_out
from attendance.services.gps import get_workspace_from_location

class IsHROrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "is_hr", False):
            return True
        return obj.employee == request.user

class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsHROrOwner]
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Attendance.objects.select_related(
            "employee", "workspace", "shift"
        ).order_by("-date")
        if getattr(user, "is_hr", False):
            return qs
        return qs.filter(employee=user)

    @extend_schema(request=ClockInSerializer)
    @action(detail=False, methods=["post"])
    def clock_in(self, request):
        serializer = ClockInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        lat = serializer.validated_data["lat"]
        lon = serializer.validated_data["lon"]
        location = Point(lon, lat, srid=4326)
        workspace = get_workspace_from_location(location)
        if not workspace:
            return Response(
                {"error": "You are not inside any workspace area"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            attendance_data = process_clock_in(
                user=user,
                workspace=workspace,
                location=location
            )
            attendance = Attendance.objects.create(**attendance_data)
            return Response({
                "message": "Clock-in successful",
                "status": attendance.status,
                "late_minutes": attendance.late_minutes,
                "is_suspicious": attendance.is_suspicious
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(request=ClockOutSerializer)
    @action(detail=False, methods=["post"])
    def clock_out(self, request):
        serializer = ClockOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        lat = serializer.validated_data["lat"]
        lon = serializer.validated_data["lon"]
        try:
            result = process_clock_out(user, lat, lon)
            return Response({
                "message": "Clock-out successful",
                "total_hours": result["total_hours"],
                "overtime_hours": result["overtime_hours"]
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(request=ClockOutSerializer)
    @action(detail=False, methods=["post"], url_path="emergency_clock_out")
    def emergency_clock_out(self, request):
        if not getattr(request.user, "is_hr", False):
            return Response(
                {"error": "Only HR can approve emergency clock out."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EmergencyClockOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee_id = serializer.validated_data["employee_id"]
        reason = serializer.validated_data["reason"]

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            employee = User.objects.get(id=employee_id)
            result = process_emergency_clock_out(
                employee=employee,
                reason=reason,
                approved_by=request.user.username
            )
            return Response(result,status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"error": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    
    @extend_schema(request=ShiftSerializer)
    @action(detail=False, methods=["get"], url_path="my_shift")
    def my_shift(self, request):
        user = request.user
        try:
            attendance = Attendance.objects.filters(
                employee=user,
                shift__isnull=False
            ).order_by("-date").first()

            if not attendance or not attendance.shift:
                return Response(
                   {"error": "No shift assigned yet"},
                   status=status.HTTP_404_NOT_FOUND
                )
            serializer = ShiftSerializer(attendance.shift)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(request=WorkspaceSerializer)
    @action(detail=False, methods=["get"], url_path="my_workspace")
    def my_workspace(self, request):
        user = request.user
        try:
            attendance = Attendance.objects.filters(
                employee=user,
                workspace__isnull=False
            ).order_by("-date").first()

            if not attendance or not attendance.workspaces:
                return Response(
                    {"error": "No workspace assigned yet"},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = WorkspaceSerializer(attendance.workspace)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class WorkspaceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsHROrOwner]
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            workspace = serializer.save()
            return Response({
                "message": "Workspace created successfully",
                "workspace_id": workspace.id,
                "name": workspace.name
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShiftViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsHROrOwner]
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer

