from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from attendance.models import Attendance
from attendance.serializers import AttendanceSerializer, ClockInSerializer, ClockOutSerializer

from attendance.services.clock_in import process_clock_in
from attendance.services.clock_out import process_clock_out
from attendance.services.gps import get_workspace_from_location


# -------------------------
# PERMISSION CLASS
# -------------------------
class IsHROrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "is_hr", False):
            return True
        return obj.employee == request.user


# -------------------------
# VIEWSET
# -------------------------
class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    READ = attendance history (HR + user filtered)
    WRITE = clock-in / clock-out via custom actions
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsHROrOwner]

    def get_queryset(self):
        user = self.request.user

        qs = Attendance.objects.select_related(
            "employee", "workspace", "shift"
        ).order_by("-date")

        if getattr(user, "is_hr", False):
            return qs

        return qs.filter(employee=user)

    # -------------------------
    # CLOCK IN
    # -------------------------
    @action(detail=False, methods=["post"])
    def clock_in(self, request):
        serializer = ClockInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        lat = serializer.validated_data["lat"]
        lon = serializer.validated_data["lon"]

        

        location = Point(lon, lat, srid=4326)

        workspace = get_workspace_from_location(location)
        # from attendance.models import Workspace

        # workspace = Workspace.objects.first()
        if not workspace:
            return Response(
                {"error": "You are not inside any workspace area"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            attendance_data = process_clock_in(
                user=user,
                workspace=workspace,
                # shift=None,  # shift is auto-selected inside service
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

    # -------------------------
    # CLOCK OUT
    # -------------------------
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

# from rest_framework import viewsets, status
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

from attendance.models import Workspace
from attendance.serializers import WorkspaceSerializer


class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    # permission_classes = [IsAuthenticated]

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
        
        

from attendance.models import Shift
from attendance.serializers import ShiftSerializer


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer

       








# from django.shortcuts import render
# from django.shortcuts import redirect
# from django.views import View
# from django.utils import timezone
# from datetime import time, datetime
# from .models import Attendance
# from rest_framework import viewsets, status, permissions
# from rest_framework.decorators import action
# from rest_framework.response import Response



# # views.py



# from .serializers import AttendanceSerializer, ClockInSerializer, ClockOutSerializer


# class AttendanceViewSet(viewsets.ModelViewSet):
#     queryset = Attendance.objects.all()

#     def get_serializer_class(self):
#         if self.action == 'clock_in':
#             return ClockInSerializer
#         elif self.action == 'clock_out':
#             return ClockOutSerializer
#         return AttendanceSerializer

#     # 🔹 CLOCK IN
#     @action(detail=False, methods=['post'])
#     def clock_in(self, request):
#         serializer = self.get_serializer(
#             data=request.data,
#             context={'request': request}  # ✅ IMPORTANT
#         )

#         if serializer.is_valid():
#             attendance = serializer.save()

#             return Response({
#                 "message": "Clock-in successful",
#                 "status": attendance.status,
#                 "late_minutes": attendance.late_minutes,
#                 "display_status": getattr(attendance, "display_status", attendance.status)
#             }, status=status.HTTP_201_CREATED)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     # 🔹 CLOCK OUT
#     @action(detail=False, methods=['post'])
#     def clock_out(self, request):
#         serializer = self.get_serializer(
#             data=request.data,
#             context={'request': request}
#         )

#         if serializer.is_valid():
#             attendance = serializer.save()

#             return Response({
#                 "message": "Clock-out successful",
#                 "total_hours": attendance.total_hours,
#                 "overtime_hours": attendance.overtime_hours
#             }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class AttendanceViewSet(viewsets.ModelViewSet):
#     queryset = Attendance.objects.all()
#     def get_serializer_class(self):
#         if self.action == 'clock_in':
#             return ClockInSerializer
#         return AttendanceSerializer
#     @action(detail=False, methods=['post'])
#     def clock_in(self, request):
#         if Attendance.objects.filter(employee=request.user, date=timezone.now().date()).exists():
#             return Response({"error": "Already clocked in."}, status=400)
        
#         serializer = self.get_serializer(data=request.data)
#         # serializer = ClockInSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"status": serializer.validated_data['status']})
#         return Response(serializer.errors, status=400)

#     @action(detail=False, methods=['post'])
#     def clock_out(self, request):
#         now = timezone.now()
#         shift_end = timezone.make_aware(datetime.combine(now.date(), time(17, 0)))
        
#         att = Attendance.objects.filter(employee=request.user, date=now.date(), clock_out_time__isnull=True).first()
#         if not att: return Response({"error": "No active clock-in."}, status=400)

#         if now < shift_end:
#             mins = int((shift_end - now).total_seconds() // 60)
#             return Response({"error": f"Shift ends in {mins} mins."}, status=403)

#         att.clock_out_time = now
#         att.exit_status = "SHIFT COMPLETED"
#         att.save()
#         return Response({"message": "Clocked out successfully."})




# class AttendanceViewSet(viewsets.ModelViewSet):
#     queryset = Attendance.objects.all()
#     permission_classes = [permissions.IsAuthenticated]

#     

#     @action(detail=False, methods=['post'])
#     def clock_in(self, request):
#         # Prevent double clock-in
#         if Attendance.objects.filter(employee=request.user, date=timezone.now().date()).exists():
#             return Response({"error": "You already clocked in today."}, status=status.HTTP_400_BAD_REQUEST)

#         serializer = self.get_serializer_class()(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"status": "Success", "attendance_status": serializer.validated_data.get('status')})
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=False, methods=['post'])
#     def clock_out(self, request):
#         now = timezone.now()
#         shift_end = timezone.make_aware(datetime.combine(now.date(), time(17, 0)))

#         attendance = Attendance.objects.filter(
#             employee=request.user, 
#             date=now.date(), 
#             clock_out_time__isnull=True
#         ).first()

#         if not attendance:
#             return Response({"error": "No active clock-in found."}, status=400)

#         if now < shift_end:
#             remaining = int((shift_end - now).total_seconds() // 60)
#             return Response({
#                 "error": "Forbidden",
#                 "message": f"Shift ends at 5PM. {remaining} minutes left."
#             }, status=status.HTTP_403_FORBIDDEN)

#         attendance.clock_out_time = now
#         attendance.exit_status = "SHIFT COMPLETED"
#         attendance.save()
#         return Response({"status": "Success", "message": "Clocked out."})

#     def get_queryset(self):
#         user = self.request.user
#         if user.is_staff or getattr(user, 'is_hr', False):
#             return Attendance.objects.all().order_by('-date')
#         return Attendance.objects.filter(employee=user).order_by('-date')




# class AttendancePermission(permissions.BasePermission):
#     message = 'Only HR are allowed.'

    
#     def has_object_permission(self, request, view, obj):
#         # Read permissions are allowed to any request,
#         # so we'll always allow GET, HEAD or OPTIONS requests.
#         if  request.employee.is_authenticated and request.employee.is_hr:
#             return True

#         # Instance must have an attribute named `owner`.
#         return obj.is_hr == request.employee
    






# class AttendanceViewSet(viewsets.ModelViewSet):
#     queryset = Attendance.objects.all()
#     permission_classes = [permissions.IsAuthenticated]

#     def get_serializer_class(self):
#         if self.action == 'clock_in': return ClockInSerializer
#         return AttendanceSerializer

#     @action(detail=False, methods=['post'])
#     def clock_in(self, request):
#         # Prevent double clock-in
#         if Attendance.objects.filter(employee__user=request.employee, date=timezone.now().date()).exists():
#             return Response({"error": "You have already clocked in for today."}, status=status.HTTP_400_BAD_REQUEST)

#         serializer = self.get_serializer_class()(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response({
#                 "status": "Success", 
#                 "attendance_status": serializer.validated_data.get('status'),
#                 "workspace": serializer.validated_data.get('workspace').name
#             }, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=False, methods=['post'])
#     def clock_out(self, request):
#         now = timezone.now()
#         shift_end = timezone.make_aware(datetime.combine(now.date(), time(17, 0))) # 5:00 PM

#         try:
#             employee = employee.objects.get(user=request.employee)
#             attendance = Attendance.objects.filter(employee=employee, date=now.date(), clock_out_time__isnull=True).first()
#         except employee.DoesNotExist:
#             return Response({"error": "Employee profile not found."}, status=400)

#         if not attendance:
#             return Response({"error": "No active clock-in found for today."}, status=400)

#         # Early Clock-out Block
#         if now < shift_end:
#             remaining = int((shift_end - now).total_seconds() // 60)
#             return Response({
#                 "error": "Access Denied", 
#                 "message": f"Shift ends at 5:00 PM. You have {remaining} minutes remaining."
#             }, status=status.HTTP_403_FORBIDDEN)

#         attendance.clock_out_time = now
#         attendance.exit_status = "SHIFT COMPLETED"
#         attendance.save()
#         return Response({"status": "Success", "message": "Clock-out recorded successfully."})


#     def get_queryset(self):
#         user = self.request.employee
#         if getattr(user, 'is_hr', False) or user.is_staff:
#             return Attendance.objects.all().order_by('-date')
#         return Attendance.objects.filter(employee=user).order_by('-date')





