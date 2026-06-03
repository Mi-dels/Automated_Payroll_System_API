from django.utils import timezone
from django.contrib.gis.geos import Point
from datetime import datetime

from rest_framework.exceptions import ValidationError
from attendance.models import Attendance


def process_clock_out(user, lat, lon):
    """
    Handles clock-out business logic
    """

    local_now = timezone.localtime()
    location = Point(lon, lat, srid=4326)

    # FIND ACTIVE RECORD 
    attendance = Attendance.objects.filter(
        employee=user,
        clock_in_time__date=local_now.date(),
        clock_out_time__isnull=True
    ).first()

    if not attendance:
        raise ValidationError("No active clock-in found.")

    #  SHIFT CHECK 
    shift = attendance.shift

    if not shift:
        raise ValidationError("Shift not found for this attendance.")

    # TIME CALCULATION 
    duration = local_now - attendance.clock_in_time
    total_hours = duration.total_seconds() / 3600

    shift_start = timezone.make_aware(
        datetime.combine(local_now.date(), shift.start_time),
        timezone.get_current_timezone()
    )
    shift_end = timezone.make_aware(
        datetime.combine(local_now.date(), shift.end_time), timezone.get_current_timezone()
    )

    shift_hours = (shift_end - shift_start).total_seconds() / 3600

    overtime_hours = max(0, total_hours - shift_hours)

    # BLOCK EARLY LEAVE
    # shift_end_aware = timezone.make_aware(shift_end)
    if local_now < shift_end:
        raise ValidationError(
            "You cannot clock out before your shift ends."
            "Contact HR for emergency early leave approval."
        )

    # DETERMINE EXIT STATUS 

    # if total_hours < shift_hours:
    #     exit_status = "EARLY LEAVE"
    if overtime_hours > 0:
        exit_status = "OVERTIME"
    else:
        exit_status = "COMPLETED"

    #  UPDATE ATTENDANCE 
    attendance.clock_out_time = local_now
    attendance.clock_out_location = location
    attendance.overtime_hours = round(overtime_hours, 2)
    attendance.exit_status = exit_status
    attendance.save()

    #  RETURN 
    return {
        "attendance": attendance,
        "total_hours": attendance.total_hours,  # computed property
        "overtime_hours": attendance.overtime_hours,
        "exit_status": exit_status
    }


def process_emergency_clock_out(employee, reason, approved_by):
    """
    HR manually clocks out an empoyee for emergency early leave
    """
    local_now = timezone.localtime()

    attendance = Attendance.objects.filter(
        employee=employee,
        clock_in_time__date=local_now.date(),
        clock_out_time__isnull=True
    ).first()

    if not attendance:
        raise ValidationError("No active clock_in found for this employee.")
    duration = local_now - attendance.clock_in_time
    total_hours = duration.total_seconds() / 3600

    attendance.clock_out_time = local_now
    attendance.overtime_hours = 0
    attendance.exit_status = f"EARLY_LEAVE - {reason}"
    attendance.save()

    return{
        "message": f"Emergency clock out approved by {approved_by}",
        "employee": employee.username,
        "total_hours": round(total_hours, 2),
        "reason": reason

    }
















# from django.utils import timezone
# from django.contrib.gis.geos import Point
# from datetime import datetime

# from rest_framework.exceptions import ValidationError
# from attendance.models import Attendance


# def process_clock_out(user, lat, lon):
#     """
#     Handles clock-out business logic
#     """

#     local_now = timezone.localtime()
#     location = Point(lon, lat, srid=4326)

#     # ---------------- FIND ACTIVE RECORD ----------------
#     attendance = Attendance.objects.filter(
#         employee=user,
#         clock_in_time__date=local_now.date(),
#         clock_out_time__isnull=True
#     ).first()

#     if not attendance:
#         raise ValidationError("No active clock-in found.")

#     # ---------------- TIME CALCULATION ----------------
#     duration = local_now - attendance.clock_in_time
#     total_hours = duration.total_seconds() / 3600

#     shift = attendance.shift

#     if not shift:
#         raise ValidationError("Shift not found for this attendance.")

#     shift_start = datetime.combine(local_now.date(), shift.start_time)
#     shift_end = datetime.combine(local_now.date(), shift.end_time)

#     shift_hours = (shift_end - shift_start).total_seconds() / 3600

#     overtime_hours = max(0, total_hours - shift_hours)

#     # ---------------- UPDATE ATTENDANCE ----------------
#     attendance.clock_out_time = local_now
#     attendance.clock_out_location = location
#     attendance.total_hours = round(total_hours, 2)
#     attendance.overtime_hours = round(overtime_hours, 2)

#     attendance.save()

#     # ---------------- RETURN CLEAN RESPONSE ----------------
#     return {
#         "attendance": attendance,
#         "total_hours": attendance.total_hours,
#         "overtime_hours": attendance.overtime_hours
#     }