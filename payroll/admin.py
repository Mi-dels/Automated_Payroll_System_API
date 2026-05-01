from django.contrib import admin
from .models import User, EmployeePreRecord, Department, JobTitle, EmploymentStatus

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """HR uses this to onboard employees and assign them to offices."""
    list_display = ('employee_id', 'username', 'full_name',  'hourly_rate')
    filter_horizontal = ('assigned_workspaces',) # The 'Drag & Drop' office selector
    
    fieldsets = (
        ('Account', {'fields': ('employee_id', 'username', 'password', 'is_hr')}),
        ('Compensation', {'fields': ('full_name', 'hourly_rate')}),
        ('Location Access', {
            'fields': ('assigned_workspaces',),
            'description': "Select which branches this employee is allowed to work from."
        }),
    )

# Register the lookup tables for HR to manage categories
admin.site.register(EmployeePreRecord)
admin.site.register(Department)
admin.site.register(JobTitle)
admin.site.register(EmploymentStatus)

# 1. Customizing the User display
# class CustomUserAdmin(UserAdmin):
#     # This controls what HR sees in the "list view"
#     list_display = ('username', 'employee_id', 'department', 'job_title', 'employment_status', 'is_hr')
#     # This adds a sidebar filter for easy sorting
#     list_filter = ('department', 'employment_status', 'is_hr')
    
#     # This allows HR to search for employees by name or ID
#     search_fields = ('username', 'first_name', 'last_name', 'employee_id')

#     # This organizes the "Edit User" page into sections
#     fieldsets = UserAdmin.fieldsets + (
#         ('Payroll & HR Info', {'fields': (
#             'employee_id', 'department', 'job_title', 'employment_status', 
#             'is_hr', 'phone_number', 'tax_id', 'bank_account_number'
#         )}),
#         ('Important Dates', {'fields': ('hire_date', 'contract_end_date', 'resignation_date')}),
#         ('Personal Info', {'fields': ('address', 'emergency_contact', 'date_of_birth')}),
#     )



# # payroll/admin.py
#  # Add this to your imports

# @admin.register(EmployeePreRecord)
# class EmployeePreRecordAdmin(admin.ModelAdmin):
#     list_display = ('employee_id', 'department', 'job_title', 'is_hr')
#     search_fields = ('employee_id',)


# # 2. Registering the dynamic models
# @admin.register(Department)
# class DepartmentAdmin(admin.ModelAdmin):
#     list_display = ('name',)

# @admin.register(JobTitle)
# class JobTitleAdmin(admin.ModelAdmin):
#     list_display = ('title', )
#     # list_filter = ('department',)

# @admin.register(EmploymentStatus)
# class EmploymentStatusAdmin(admin.ModelAdmin):
#     list_display = ('name',)

# # Register the Custom User
# admin.site.register(User, CustomUserAdmin)

