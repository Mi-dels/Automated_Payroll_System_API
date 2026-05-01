from rest_framework import serializers
from .models import Attendance, Workspace, Shift
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils import timezone
from datetime import time, datetime
from .constant import AttendanceStatus

# serializers.py

User = get_user_model()





from attendance.services.clock_in import process_clock_in






# attendance/serializers.py

from rest_framework import serializers


class ClockInSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()

    def validate(self, data):
        if not (-90 <= data["lat"] <= 90):
            raise serializers.ValidationError("Invalid latitude")

        if not (-180 <= data["lon"] <= 180):
            raise serializers.ValidationError("Invalid longitude")

        return data
    

   
from attendance.services.clock_out import process_clock_out



class ClockOutSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()

    def validate(self, data):
        if not (-90 <= data["lat"] <= 90):
            raise serializers.ValidationError("Invalid latitude")

        if not (-180 <= data["lon"] <= 180):
            raise serializers.ValidationError("Invalid longitude")

        return data




from rest_framework import serializers
from django.contrib.gis.geos import Point
from attendance.models import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(write_only=True)
    lon = serializers.FloatField(write_only=True)

    shifts = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Shift.objects.all()
    )

    class Meta:
        model = Workspace
        fields = [
            "id",
            "name",
            "lat",
            "lon",
            "radius_meters",
            "shifts"
        ]

    def create(self, validated_data):
        lat = validated_data.pop("lat")
        lon = validated_data.pop("lon")

        shifts = validated_data.pop("shifts")

        validated_data["location"] = Point(lon, lat, srid=4326)

        workspace = Workspace.objects.create(**validated_data)

        # attach shifts properly
        workspace.shifts.set(shifts)

        return workspace

    def update(self, instance, validated_data):
        lat = validated_data.pop("lat", None)
        lon = validated_data.pop("lon", None)

        shifts = validated_data.pop("shifts", None)

        if lat is not None and lon is not None:
            instance.location = Point(lon, lat, srid=4326)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # update shifts properly
        if shifts is not None:
            instance.shifts.set(shifts)

        return instance


# class WorkspaceSerializer(serializers.ModelSerializer):
#     lat = serializers.FloatField(write_only=True)
#     lon = serializers.FloatField(write_only=True)

#     class Meta:
#         model = Workspace
#         fields = ["id", "name", "lat", "lon", "radius_meters", "shifts"]

#     def create(self, validated_data):
#         lat = validated_data.pop("lat")
#         lon = validated_data.pop("lon")
#         shifts = serializers.PrimaryKeyRelatedField(
#             many=True,
#             queryset=Shift.objects.all()
#         )

#         validated_data["location"] = Point(lon, lat, srid=4326)

#         workspace = Workspace.objects.create(**validated_data)

#         # ✅ THIS IS THE FIX
#         workspace.shifts.set(shifts)

#         return workspace

#     def update(self, instance, validated_data):
#         lat = validated_data.pop("lat", None)
#         lon = validated_data.pop("lon", None)
#         shifts = validated_data.pop("shifts", None)

#         if lat is not None and lon is not None:
#             instance.location = Point(lon, lat, srid=4326)

#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)

#         instance.save()

#         # ✅ THIS IS THE FIX
#         if shifts is not None:
#             instance.shifts.set(shifts)

#         return instance
    






class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ["id", "name", "start_time", "end_time", "grace_minutes"]

    def validate(self, data):
        start = data["start_time"]
        end = data["end_time"]

        # Optional safety check (prevents exact same time)
        if start == end:
            raise serializers.ValidationError("Start and end time cannot be the same")

        return data


    class AttendanceSerializer(serializers.ModelSerializer):
        total_hours = serializers.ReadOnlyField()

        class Meta:
            model = Attendance
            fields = [
                "id",
                "employee",
                "workspace",
                "shift",
                "date",
                "clock_in_time",
                "clock_out_time",
                "status",
                "late_minutes",
                "overtime_hours",
                "total_hours",
                "is_suspicious"
            ]




    # def validate(self, data):
    #     user = self.context['request'].user
    #     user_location = Point(data['lon'], data['lat'], srid=4326)
    #     local_now = timezone.localtime()

    #     # Geofencing multiple workspaces
    #     assigned_ws = user.assigned_workspaces.all()
    #     active_ws = assigned_ws.first()

    #     if not active_ws:
    #         raise serializers.ValidationError("No workspace assigned.")

    #     #
    #     # active_ws = next((ws for ws in assigned_ws if ws.location.distance(user_location) <= ws.radius_meters), None)
        
    #     # if not active_ws:
    #     #     raise serializers.ValidationError("You are not at an authorized workspace.")

    #     # Lateness Logic
    #     # now = timezone.now()
    #     # shift_start = timezone.make_aware(datetime.combine(now.date(), time(8, 0)))

    #      # 🔹 SHIFT LOGIC
    #     shift = active_ws.shift
    #     shift_start = local_now.replace(
    #         hour=shift.start_time.hour,
    #         minute=shift.start_time.minute,
    #         second=0,
    #         microsecond=0
    #     )

        

    #     late_mins = int((local_now - shift_start).total_seconds() // 60)

    #     if late_mins <= 0:
    #         status_label = AttendanceStatus.PRESENT
    #     elif late_mins <= 5:
    #         status_label = AttendanceStatus.GRACE
    #     else:
    #         status_label = AttendanceStatus.LATE

        
    #     # 🔹 GPS SPOOF CHECK
    #     last_attendance = Attendance.objects.filter(employee=user).order_by('-clock_in_time').first()

    #     is_suspicious = False
    #     if last_attendance:
    #         time_diff = (local_now - last_attendance.clock_in_time).total_seconds() / 3600
    #         distance = last_attendance.clock_in_location.distance(user_location)

    #         if time_diff > 0:
    #             speed = distance / time_diff
    #             if speed > 200:  # unrealistic speed (km/h threshold idea)
    #                 is_suspicious = True


        

    #     data.update({
    #         'employee': user,
    #         'workspace': active_ws,
    #         'shift': shift,
    #         'clock_in_time': local_now,   # ✅ use same timezone
    #         'clock_in_location': user_location,
    #         'status': status_label,
    #         'late_minutes': late_mins if late_mins > 0 else 0,
    #         'is_suspicious': is_suspicious,
    #     })

    #     return data
    

    # def get_display_status(self, obj):
    #     if obj.status == AttendanceStatus.LATE:
    #         return f"LATE ({obj.late_minutes} mins)"
    #     return obj.get_status_display()

    # def create(self, validated_data):
    #     validated_data.pop('lat'); validated_data.pop('lon')
    #     return Attendance.objects.create(**validated_data)
    



# class ClockOutSerializer(serializers.Serializer):
#     lat = serializers.FloatField()
#     lon = serializers.FloatField()

#     def validate(self, data):
#         user = self.context['request'].user
#         user_location = Point(data['lon'], data['lat'], srid=4326)
#         local_now = timezone.localtime()

#         attendance = Attendance.objects.filter(
#             employee=user,
#             clock_in_time__date=local_now.date(),
#             clock_out_time__isnull=True
#         ).first()

#         if not attendance:
#             raise serializers.ValidationError("No active clock-in found.")

#         duration = local_now - attendance.clock_in_time
#         total_hours = duration.total_seconds() / 3600

#         shift_hours = (
#             datetime.combine(local_now.date(), attendance.shift.end_time) -
#             datetime.combine(local_now.date(), attendance.shift.start_time)
#         ).total_seconds() / 3600

#         overtime = max(0, total_hours - shift_hours)

#         data.update({
#             'attendance': attendance,
#             'clock_out_time': local_now,
#             'clock_out_location': user_location,
#             'total_hours': round(total_hours, 2),
#             'overtime_hours': round(overtime, 2)
#         })

#         return data

#     def save(self, **kwargs):
#         attendance = self.validated_data['attendance']

#         attendance.clock_out_time = self.validated_data['clock_out_time']
#         attendance.clock_out_location = self.validated_data['clock_out_location']
#         attendance.total_hours = self.validated_data['total_hours']
#         attendance.overtime_hours = self.validated_data['overtime_hours']

#         attendance.save()
#         return attendance





class AttendanceSerializer(serializers.ModelSerializer):
    total_hours = serializers.ReadOnlyField()
    class Meta:
        model = Attendance
        fields = ['id', 'employee', 'date', 'clock_in_time', 'clock_out_time', 'status', 'exit_status', 'total_hours']

        

# class ClockInSerializer(serializers.ModelSerializer):
#     lat = serializers.FloatField(write_only=True)
#     lon = serializers.FloatField(write_only=True)

#     class Meta:
#         model = Attendance
#         fields = ['lat', 'lon']

#     def validate(self, data):
#         user = self.context['request'].user # Standard way to get the logged-in user
        
#         # 1. Geofencing check
#         user_location = Point(data['lon'], data['lat'], srid=4326)
#         # Access assigned_workspaces defined in your custom User model
#         assigned_ws = user.assigned_workspaces.all()
        
#         if not assigned_ws.exists():
#             raise serializers.ValidationError("You have not been assigned to any workspaces by HR.")

#         active_ws = None
#         for ws in assigned_ws:
#             if ws.location.distance(user_location) <= ws.radius_meters:
#                 active_ws = ws
#                 break
        
#         if not active_ws:
#             raise serializers.ValidationError("You are not within the radius of any assigned workspace.")

#         # 2. Timing Logic
#         now = timezone.now()
#         shift_start = timezone.make_aware(datetime.combine(now.date(), time(8, 0)))
#         grace_period = 5
#         late_minutes = int((now - shift_start).total_seconds() // 60)

#         if late_minutes <= 0:
#             status_label = 'PRESENT'
#         elif late_minutes <= grace_period:
#             status_label = 'PRESENT (Grace Period)'
#         else:
#             status_label = f'LATE ({late_minutes} mins)'

#         data['employee'] = user
#         data['workspace'] = active_ws
#         data['clock_in_time'] = now
#         data['clock_in_location'] = user_location
#         data['status'] = status_label
#         return data

#     def create(self, validated_data):
#         validated_data.pop('lat')
#         validated_data.pop('lon')
#         return Attendance.objects.create(**validated_data)


# class WorkspaceSerialier(serializers.ModelSerializer):


#     class Meta:
#         model = Workspace
#         fields = ['name', 'location', 'radius_meters']


# class EmployeeSerializers(serializers.ModelSerializer):


#     class Meta:
#         model = Employee
#         fields = '_all_'



# class AttendanceSerializer(serializers.ModelSerializer):
#     total_hours = serializers.ReadOnlyField()
#     employee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

#     class Meta:
#         model = Attendance
#         fields = ['id', 'employee',  'date', 'clock_in_time', 'clock_out_time', 'status', 'exit_status', 'total_hours']

# class ClockInSerializer(serializers.ModelSerializer):
#     lat = serializers.FloatField(write_only=True)
#     lon = serializers.FloatField(write_only=True)

#     class Meta:
#         model = Attendance
#         fields = ['lat', 'lon']

#     def validate(self, data):
#         user = self.context['request'].employee
        
#         # 1. Get Employee Instance (Fixes your IdentityError)
#         try:
#             employee = Employee.objects.get(user=employee)
#         except Employee.DoesNotExist:
#             raise serializers.ValidationError("Employee profile not found for this user.")

#         # 2. Get Workspace (Using first available or specific logic)

#         user_location = Point(data['lon'], data['lat'], srid=4326)
#         assigned_ws = employee.assigned_workspaces.all()
        
#         if not assigned_ws.exists():
#             raise serializers.ValidationError("You have not been assigned to any workspaces by HR.")

#         active_ws = None
#         for ws in assigned_ws:
#             if ws.location.distance(user_location) <= ws.radius_meters:
#                 active_ws = ws
#                 break
        
#         if not active_ws:
#             raise serializers.ValidationError("Location Error: You are not within the radius of any assigned workspace.")

#         # workspace = Workspace.objects.filter(user=user).first() or Workspace.objects.first()
#         # if not workspace:
#         #     raise serializers.ValidationError("No workspace setup available.")

#         # # 3. Geofencing
#         # user_location = Point(data['lon'], data['lat'], srid=4326)
#         # distance = workspace.location.distance(user_location)
#         # if distance > workspace.radius_meters:
#         #     raise serializers.ValidationError(f"Too far! You are {int(distance)}m away from {workspace.name}.")

#         # 4. Timing & Status Logic
#         now = timezone.now()
#         shift_start = timezone.make_aware(datetime.combine(now.date(), time(8, 0))) # 8:00 AM
#         grace_period = 5
        
#         late_delta = now - shift_start
#         late_minutes = int(late_delta.total_seconds() // 60)

#         if late_minutes <= 0:
#             status_label = 'PRESENT'
#         elif late_minutes <= grace_period:
#             status_label = 'PRESENT (Grace Period)'
#         else:
#             status_label = f'LATE ({late_minutes} mins)'

#         # 5. Pack data for the create() method
#         data['employee'] = employee
#         data['workspace'] = Workspace
#         data['clock_in_time'] = now
#         data['clock_in_location'] = user_location
#         data['status'] = status_label
        
#         return data

#     def create(self, validated_data):
#         # Remove lat/lon so they don't crash the Attendance.objects.create
#         validated_data.pop('lat')
#         validated_data.pop('lon')
#         return Attendance.objects.create(**validated_data)


# 


# class AttendanceSerializer(serializers.ModelSerializer):
#     # Read-only field to show the calculated total_hours in the API
#     total_hours = serializers.ReadOnlyField()
#     employee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

#     class Meta:
#         model = Attendance
#         fields = ['id', 'employee','date', 'clock_in_time', 'clock_out_time', 'status', 'total_hours']
#         read_only_fields = ['date'] # Date is usually set automatically




# class ClockInSerializer(serializers.ModelSerializer):
#     lat = serializers.FloatField(write_only=True)
#     lon = serializers.FloatField(write_only=True)

#     class Meta:
#         model = Attendance
#         fields = ['lat', 'lon'] # Nothing else needed from frontend

#     def validate(self, data):
#         user = self.context['request'].user
        
#         # 1. Look for the workspace assigned to this user
#         workspace = user.assigned_workspace
        
#         if not workspace:
#             raise serializers.ValidationError("No workspace assigned to your profile. Please contact HR.")

#         # 2. Create the point from user's current GPS
#         user_location = Point(data['lon'], data['lat'], srid=4326)

#         # 3. Calculate distance (PostGIS geography returns meters)
#         distance = workspace.location.distance(user_location)

#         if distance > workspace.radius_meters:
#             raise serializers.ValidationError({
#                 "location_error": f"You are {int(distance)}m away from {workspace.name}. Move closer to clock in."
#             })

#         # Attach these so they get saved in the Attendance record


          




#         now = timezone.now()
#         today = now.date()
#         shift_start = timezone.make_aware(datetime.combine(today, time(8, 0)))
#         shift_end = timezone.make_aware(datetime.combine(today, time(17, 0)))
#         GRACE_PERIOD_MINS = 5

#         # --- CLOCK IN LOGIC ---
#         if not data.get('clock_in_time'):
#         # This logic usually runs when the user hits 'Clock In'
#             data['clock_in_time'] = now
    
#             late_delta = now - shift_start
#             late_minutes = int(late_delta.total_seconds() // 60)

#         if late_minutes <= 0:
#             data['status'] = 'PRESENT'
#         elif late_minutes <= GRACE_PERIOD_MINS:
#             data['status'] = f'PRESENT (Grace Period)'
#         else:
#             data['status'] = f'LATE ({late_minutes} mins)'

# # --- CLOCK OUT LOGIC ---
# # Run this when the user attempts to click the 'Clock Out' button
#         def handle_clock_out(user_record):
#             now = timezone.now()
    
#             if now < shift_end:
#                 remaining_delta = shift_end - now
#                 remaining_minutes = int(remaining_delta.total_seconds() // 60)
        
#               # Block the action and return the message
#                 return {
#                     "error": True,
#                     "message": f"You cannot clock out yet. Work time ends in {remaining_minutes} minutes."
#                 }
    
#                # If time is past shift_end, allow clock out
#             user_record['clock_out_time'] = now
#             user_record['exit_status'] = "SHIFT COMPLETED"
#             return {"error": False, "data": user_record}

# # --- ABSENCE CHECK ---
# # Logic for a background task or report at the end of the day
#         if not data.get('clock_in_time') and now.time() > shift_end.time():
#             data['status'] = 'ABSENT'

       
    

#     def create(self, validated_data):
#         validated_data.pop('lat')
#         validated_data.pop('lon')
#         # Record who is clocking in
#         validated_data['employee'] = self.context['request'].user
#         return super().create(validated_data)

 # now = timezone.now()
        # shift_start = time(8) # 08:05 AM - Change this to your office start time
        # data['clock_in_time'] = now 

        # if now.time() > shift_start:
        #     data['status'] = 'LATE'
        # else:
        #     data['status'] = 'PRESENT'

        

        # data['clock_in_location'] = user_location
        # data['workspace'] = workspace
        # # Immediate server time
        # return data
        # 
        # 
# class ClockInSerializer(serializers.ModelSerializer):
#     # These are for the frontend to send the user's current GPS
#     lat = serializers.FloatField(write_only=True)
#     lon = serializers.FloatField(write_only=True)

#     class Meta:
#         model = Attendance
#         fields = ['workspace', 'lat', 'lon']

#     def validate(self, data):
#         workspace = data['workspace']
#         # Create a Point object (Note: GeoJSON uses Longitude first)
#         user_location = Point(data['lon'], data['lat'], srid=4326)

#         # THE MAGIC LINE: Calculate distance in meters
#         # distance() returns a value we compare against the workspace radius
#         distance_meters = workspace.location.distance(user_location) * 1000000 # Scaling for geography

#         if distance_meters > workspace.radius_meters:
#             raise serializers.ValidationError({
#                 "location_error": f"You are {int(distance_meters)}m away. Please move closer to {workspace.name}."
#             })

#         # Attach the location object so it gets saved to the DB
#         data['clock_in_location'] = user_location
#         # Remove the raw floats before saving
#         data.pop('lat')
#         data.pop('lon')

# class AttendanceSerializer(serializers.ModelSerializer):
#     # This ensures the dropdown shows all users from your custom User model
#     user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
#     total_hours = serializers.ReadOnlyField()
#     employee_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
#     class Meta:
#         model = Attendance
#         fields = ['id', 'user', 'date', 'check_in', 'check_out', 'status', 'total_hours']


