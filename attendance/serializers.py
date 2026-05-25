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








class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ["id", "name", "start_time", "end_time", "grace_minutes","hourly_rate",
        "late_penalty_per_minute","overtime_rate_multiplier"]

    def validate(self, data):
        start = data["start_time"]
        end = data["end_time"]

        # Optional safety check (prevents exact same time)
        if start and end and start == end:
            raise serializers.ValidationError("Start and end time cannot be the same")

        return data


class AttendanceSerializer(serializers.ModelSerializer):
    total_hours = serializers.FloatField(read_only=True)

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







# class AttendanceSerializer(serializers.ModelSerializer):
#     total_hours = serializers.ReadOnlyField()
#     class Meta:
#         model = Attendance
#         fields = ['id', 'employee', 'date', 'clock_in_time', 'clock_out_time', 'status', 'exit_status', 'total_hours']

        

