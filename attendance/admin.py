# Register your models here.
from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from .models import Workspace, Attendance
from leaflet.admin import LeafletGeoAdmin

@admin.register(Workspace)
class WorkspaceAdmin(LeafletGeoAdmin): # Much better for streets
    list_display = ('name', 'radius_meters')

    # Interactive map settings
     # Leaflet settings for the Admin map
    # settings_overrides = {
    #     'DEFAULT_CENTER': (6.5244, 3.3792), # Lagos center
    #     'DEFAULT_ZOOM': 12,
    #     'MIN_ZOOM': 3,
    #     'MAX_ZOOM': 20, # Allows HR to see street-level detail
    # }
    change_form_template = 'change_form.html'
    # class Media:

    #     css = {
    #         'all': ('https://unpkg.com',)
    #     }
         
    #     js = (
    #         'https://unpkg.com',
    #     # Make sure this name matches your file!
    #     )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """HR uses this to audit who came late or left early."""
    list_display = ('employee', 'date', 'status', 'total_hours', 'workspace')
    list_filter = ('status', 'date', 'workspace')
    readonly_fields = ('clock_in_time', 'clock_out_time', 'clock_in_location', 'date')
    
    fieldsets = (
        ('Basic Info', {'fields': ('employee', 'workspace', 'date')}),
        ('Timing', {'fields': ('status', 'exit_status', 'clock_in_time', 'clock_out_time')}),
        ('GPS Data', {'fields': ('clock_in_location',), 'classes': ('collapse',)}),
    )

# @admin.register(Workspace)
# class WorkspaceAdmin(gis_admin.GISModelAdmin):
#     """HR uses this to set the geofence for each office."""
#     list_display = ('name', 'radius_meters')

 # gis_widget_kwargs = {
    #     'attrs': {
    #         'default_zoom': 12,
    #         'default_lat': 6.5244, # Lagos Lat
    #         'default_lon': 3.3792, # Lagos Lon
    #     }
    # }
