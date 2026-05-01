from django.utils import timezone


def get_active_shift(workspace):
    """
    Determine which shift is currently active for a workspace
    """
    now = timezone.localtime()

    buffer_minutes = 10

    
    for shift in workspace.shifts.all():

        start = now.replace(
            hour=shift.start_time.hour,
            minute=shift.start_time.minute,
            second=0,
            microsecond=0
        )

        end = now.replace(
            hour=shift.end_time.hour,
            minute=shift.end_time.minute,
            second=0,
            microsecond=0
        )
        start = start - timezone.timedelta(minutes=buffer_minutes)
        end = end + timezone.timedelta(minutes=buffer_minutes)

       # 🔥 HANDLE NIGHT SHIFTS (IMPORTANT)
        if shift.end_time < shift.start_time:
            if now >= start or now <= end:
                return shift
        else:
            if start <= now <= end:
                return shift

    return None