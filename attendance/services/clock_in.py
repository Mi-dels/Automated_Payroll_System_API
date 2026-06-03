from django.utils import timezone
import datetime
from rest_framework.exceptions import ValidationError

from attendance.models import Attendance
from attendance.constant import AttendanceStatus
from attendance.services.gps import is_suspicious_movement
from attendance.services.shift_selector import get_active_shift


def process_clock_in(user, workspace, location):
    """
    Handles all business logic for clock-in
    """

    if not workspace:
        raise ValidationError("No valid workspace found.")

    if not workspace.shifts.exists():
        raise ValidationError("No shift assigned to this workspace.")

    # pick first shift (you can improve later)
    # shift = workspace.shifts.first()

    shift = get_active_shift(workspace)
    if not shift:
        raise ValidationError("No active shift at this time. Please check your shift schedule.")

    # print("Workspace ID:", workspace.id)
    # print("Workspace shifts:", workspace.shifts.all())

    local_now = timezone.localtime()

    # GEO FENCE 
    # GeoDjango distance returns degrees → convert to meters approx
    # distance = workspace.location.distance(location) * 100000

    # if distance > workspace.radius_meters:
    #     raise ValidationError("You are outside the workspace area.")

    # SHIFT LOGIC 
    # shift_start = local_now.replace(
    #     hour=shift.start_time.hour,
    #     minute=shift.start_time.minute,
    #     second=0,
    #     microsecond=0
    # )
    shift_start_native = datetime.datetime.combine(
        local_now.date(),
        shift.start_time
    )
    shift_start_utc = timezone.make_aware(shift_start_native, datetime.timezone.utc)
    shift_start = timezone.localtime(shift_start_utc)
    #debug remove after fixing
    print(f"NOW LOCAL: {local_now}")
    print(f"SHIFT START : {shift_start}")
    print(f"SHIFT START TIME FROM DB : {shift.start_time}")
    print(f"DIFF MINUTES : {(local_now - shift_start).total_seconds() // 60}")

    

    late_mins = max(
    0,
    int((local_now - shift_start).total_seconds() // 60)
    )

    if late_mins <= 0:
        status = AttendanceStatus.PRESENT
    elif late_mins <= shift.grace_minutes:
        status = AttendanceStatus.GRACE
    else:
        status = AttendanceStatus.LATE

    # SUSPICIOUS CHECK
    last_attendance = Attendance.objects.filter(
        employee=user,
        clock_in_time__isnull=False,
        clock_in_location__isnull=False
    ).order_by("-clock_in_time").first()

    is_suspicious = False

    if last_attendance:
        time_diff = (local_now - last_attendance.clock_in_time).total_seconds() / 3600

        if time_diff > 0:
            is_suspicious = is_suspicious_movement(
                last_location=last_attendance.clock_in_location,
                new_location=location,
                time_diff_hours=time_diff
            )

    # RETURN CLEAN DATA 
    return {
        "employee": user,
        "workspace": workspace,
        "shift": shift,
        "clock_in_time": local_now,
        "clock_in_location": location,
        "status": status,
        "late_minutes": max(late_mins, 0),
        "is_suspicious": is_suspicious,

       
    } 
   