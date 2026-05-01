from attendance.models import Attendance


def calculate_absent_days(user, year, month, expected_working_days=22):

    attended_days = Attendance.objects.filter(
        employee=user,
        clock_in_time__year=year,
        clock_in_time__month=month,
        clock_out_time__isnull=False
    ).values("clock_in_time__date").distinct().count()

    absent_days = max(0, expected_working_days - attended_days)

    return {
        "attended_days": attended_days,
        "absent_days": absent_days
    }