from django.contrib.gis.geos import Point



from django.contrib.gis.db.models.functions import Distance

def get_workspace_from_location(location):
    from attendance.models import Workspace

    # annotate each workspace with real distance
    workspaces = Workspace.objects.annotate(
        distance=Distance("location", location)
    ).order_by("distance")

    for workspace in workspaces:
        # distance is now in meters (properly handled)
        if workspace.distance.m <= workspace.radius_meters:
            if workspace.shifts.exists():
                return workspace

    return None
    
def calculate_speed(distance_km, time_hours):
    if time_hours <= 0:
        return 0
    return distance_km / time_hours


def is_suspicious_movement(last_location, new_location, time_diff_hours):
    """
    Simple fraud detection logic (capstone-ready version)
    """

    if not last_location or not new_location:
        return False

    # distance in degrees → approximate conversion (simple version for capstone)
    distance_km = last_location.distance(new_location) * 111  # rough km conversion

    speed = calculate_speed(distance_km, time_diff_hours)

    # 🚨 threshold: human cannot realistically exceed this regularly
    if speed > 120:  # km/h
        return True

    return False