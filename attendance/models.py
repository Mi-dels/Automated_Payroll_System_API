# from django.db import models
from django.conf import settings
# from payroll.models import Department, JobTitle, EmploymentStatus, EmployeePreRecord 
import datetime
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models  # MUST use this for GIS
from django.utils import timezone
from django.conf import settings
from .constant import AttendanceStatus


# second_app/models.py
class Shift(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_minutes = models.IntegerField(default=5)

    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
        help_text="Override default hourly rate for this shift.")
    late_penalty_per_minute = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Override default late penalty per minute for this shift. ")
    overtime_rate_multiplier = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Override default overtime rate multiplier for this shift.")

    def __str__(self):
        return self.name
    


STATUS_CHOICES = [
    (AttendanceStatus.PRESENT, "Present"),
    (AttendanceStatus.GRACE, "Grace"),
    (AttendanceStatus.LATE, "Late"),
    (AttendanceStatus.ABSENT, "Absent"),
]

    


class Workspace(models.Model):
    # Link to your custom User model via string to avoid circular imports
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='owned_workspaces', 
        null=True, 
        blank=True
    )
    # Workspace
    shifts = models.ManyToManyField(Shift, related_name="workspaces",blank=True)
    name = models.CharField(max_length=255, default="Main Office")
    location = models.PointField(geography=True, srid=4326)
    radius_meters = models.PositiveIntegerField(default=200)
    
    def __str__(self):
        return self.name

class Attendance(models.Model):
    # ForeignKey instead of OneToOne allows multiple days of attendance
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='user_attendances',
        null=True
    )
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True)

    date = models.DateField(auto_now_add=True)
    clock_in_time = models.DateTimeField(null=True, blank=True)
    clock_out_time = models.DateTimeField(null=True, blank=True)

    clock_out_location = models.PointField(null=True, blank=True)
    clock_in_location = models.PointField(geography=True, srid=4326, null=True, blank=True)

    # total_hours = models.FloatField( default=0,null=True, blank=True)
    late_minutes = models.IntegerField(null=True, blank=True)
    overtime_hours = models.FloatField(null=True, blank=True)

    is_suspicious = models.BooleanField(default=False)  # 👈 GPS spoof flag

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=AttendanceStatus.PRESENT
    )
    exit_status = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'date')

    @property
    def total_hours(self):
        if self.clock_in_time and self.clock_out_time:
            delta = self.clock_out_time - self.clock_in_time
            return round(delta.total_seconds() / 3600, 2)
        return 0.0

    def __str__(self):
        # Accessing employee_id from your custom User model
        eid = getattr(self.employee, 'employee_id', 'No ID')
        return f"{eid} - {self.date}"



