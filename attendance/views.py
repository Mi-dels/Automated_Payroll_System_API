# from rest_framework import viewsets, status, permissions
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from django.contrib.gis.geos import Point
# from attendance.models import Attendance
# from attendance.serializers import AttendanceSerializer, ClockInSerializer, ClockOutSerializer
# from rest_framework.permissions import (
#     IsAuthenticated
# )
# from attendance.services.clock_in import process_clock_in
# from attendance.services.clock_out import process_clock_out
# from attendance.services.gps import get_workspace_from_location


# # -------------------------
# # PERMISSION CLASS
# # -------------------------
# class IsHROrOwner(permissions.BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated

#     def has_object_permission(self, request, view, obj):
#         if getattr(request.user, "is_hr", False):
#             return True
#         return obj.employee == request.user


# # -------------------------
# # VIEWSET
# # -------------------------
# class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     READ = attendance history (HR + user filtered)
#     WRITE = clock-in / clock-out via custom actions
#     """
#     permission_classes = [ IsAuthenticated,IsHROrOwner]
#     queryset = Attendance.objects.all()
#     serializer_class = AttendanceSerializer
    

#     def get_queryset(self):
#         user = self.request.user

#         qs = Attendance.objects.select_related(
#             "employee", "workspace", "shift"
#         ).order_by("-date")

#         if getattr(user, "is_hr", False):
#             return qs

#         return qs.filter(employee=user)

#     # -------------------------
#     # CLOCK IN
#     # -------------------------
#     @action(detail=False, methods=["post"])
#     def clock_in(self, request):
#         serializer = ClockInSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = request.user
#         lat = serializer.validated_data["lat"]
#         lon = serializer.validated_data["lon"]

        

#         location = Point(lon, lat, srid=4326)

#         workspace = get_workspace_from_location(location)
#         # from attendance.models import Workspace

#         # workspace = Workspace.objects.first()
#         if not workspace:
#             return Response(
#                 {"error": "You are not inside any workspace area"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             attendance_data = process_clock_in(
#                 user=user,
#                 workspace=workspace,
#                 # shift=None,  # shift is auto-selected inside service
#                 location=location
#             )

#             attendance = Attendance.objects.create(**attendance_data)

#             return Response({
#                 "message": "Clock-in successful",
#                 "status": attendance.status,
#                 "late_minutes": attendance.late_minutes,
#                 "is_suspicious": attendance.is_suspicious
#             }, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             return Response(
#                 {"error": str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#     # -------------------------
#     # CLOCK OUT
#     # -------------------------
#     @action(detail=False, methods=["post"])
#     def clock_out(self, request):
#         serializer = ClockOutSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = request.user
#         lat = serializer.validated_data["lat"]
#         lon = serializer.validated_data["lon"]

#         try:
#             result = process_clock_out(user, lat, lon)

#             return Response({
#                 "message": "Clock-out successful",
#                 "total_hours": result["total_hours"],
#                 "overtime_hours": result["overtime_hours"]
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response(
#                 {"error": str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )


# from attendance.models import Workspace
# from attendance.serializers import WorkspaceSerializer


# class WorkspaceViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated, IsHROrOwner ]
#     queryset = Workspace.objects.all()
#     serializer_class = WorkspaceSerializer
    

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)

#         if serializer.is_valid():
#             workspace = serializer.save()

#             return Response({
#                 "message": "Workspace created successfully",
#                 "workspace_id": workspace.id,
#                 "name": workspace.name
#             }, status=status.HTTP_201_CREATED)
            
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        

# from attendance.models import Shift
# from attendance.serializers import ShiftSerializer


# class ShiftViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated, IsHROrOwner ]
#     queryset = Shift.objects.all()
#     serializer_class = ShiftSerializer

       








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
)
from attendance.services.clock_in import process_clock_in
from attendance.services.clock_out import process_clock_out
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

