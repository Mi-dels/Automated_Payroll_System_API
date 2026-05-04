from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.conf import settings
from attendance.models import Attendance, AttendanceStatus
from decimal import Decimal
from django.utils import timezone
import datetime
# only HR uses the pages.





class Department(models.Model):
    name = models.CharField(max_length=100, null=True)
    def __str__(self): return self.name

class JobTitle(models.Model):
    title = models.CharField(max_length=100, null=True)
    def __str__(self): return self.title

class EmploymentStatus(models.Model):
    name = models.CharField(max_length=50, null=True)
    def __str__(self): return self.name

class EmployeePreRecord(models.Model):
    employee_id = models.CharField(max_length=20, unique=True, null=True)
    job_title = models.ForeignKey(JobTitle, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    employment_status = models.ForeignKey(EmploymentStatus, on_delete=models.SET_NULL, null=True, blank=True)
    hire_date = models.DateField(null=True)
    is_hr = models.BooleanField(default=False)
    
    
    def __str__(self):
        return f"{self.employee_id}"

class User(AbstractUser):
    

    ROLE_CHOICES = [
        ("EMPLOYEE", "Employee"),
        ("HR", "HR"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="EMPLOYEE"
    )



    # FIX: Use string 'attendance.Workspace' to avoid circular import error
    assigned_workspaces = models.ManyToManyField(
        'attendance.Workspace', 
        related_name='employees', 
        blank=True
    )
    
    employee_id = models.CharField(max_length=20, unique=True, null=True)
    hr_profile = models.OneToOneField(
        EmployeePreRecord, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True
    )
    is_hr = models.BooleanField(default=False, null=True)
    date_of_birth = models.DateField(null=True)
    # Personal info
    full_name = models.CharField(max_length=100, null=True)
    address = models.TextField(null=True, max_length=100)
    phone_number = models.CharField(max_length=20, unique=True, null=True)
    emergency_contact = models.CharField(null=True, max_length=50)
    tax_id = models.CharField(max_length=50, unique=True, null=True)
    bank_account_number = models.CharField( max_length=50, null=True, unique=True)
    bank_code = models.CharField(max_length=10, null=True, blank=True, help_text="e.g., 057 for Zenith, 999992 for OPay")
    paystack_recipient_code = models.CharField(max_length=50, blank=True, null=True)

    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

       
    

    def save(self, *args, **kwargs):
        if not self.pk and self.employee_id:
            try:
                record = EmployeePreRecord.objects.get(employee_id=self.employee_id)
                self.is_hr = record.is_hr
                self.hr_profile = record
            except EmployeePreRecord.DoesNotExist:
                raise ValidationError("Employee ID not found in HR records.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.employee_id})"
    










from django.db import models
from django.conf import settings


class PayrollPeriod(models.Model):
    month = models.DateField(unique=True)  # use first day of month e.g. 2026-04-01
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return self.month.strftime('%B %Y')


class PayrollConfiguration(models.Model):
    late_penalty_flat_rate = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    overtime_rate_multiplier = models.FloatField(default=1.5)

    class Meta:
        verbose_name = "Payroll Configuration"



class Salary(models.Model):

    PAYMENT_STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("APPROVED", "Approved"),
        ("PAID", "Paid"),
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="salaries"
    )

    period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.PROTECT
    )

    # =========================
    # ATTENDANCE SNAPSHOT
    # =========================
    total_hours = models.FloatField(default=0.0)

    overtime_hours = models.FloatField(default=0.0)

    late_instances_count = models.IntegerField(default=0)

    # =========================
    # PAY SNAPSHOT
    # =========================
    hourly_rate_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    gross_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    lateness_deduction = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    net_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    # =========================
    # PAYMENT WORKFLOW
    # =========================
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="DRAFT"
    )

    is_paid = models.BooleanField(default=False)

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # =========================
    # TIMESTAMPS
    # =========================
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.employee} - {self.period}"






# class Salary(models.Model):
#     employee = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='salaries'
#     )

#     period = models.ForeignKey(PayrollPeriod, on_delete=models.PROTECT)

#     total_hours = models.FloatField(default=0.0)
#     overtime_hours = models.FloatField(default=0.0)
#     late_instances_count = models.IntegerField(default=0)

#     hourly_rate_snapshot = models.DecimalField(max_digits=10, decimal_places=2)

#     gross_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     lateness_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
#     net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

#     is_paid = models.BooleanField(default=False)
#     transaction_reference = models.CharField(max_length=100, blank=True, null=True)
#     payment_status = models.CharField(max_length=20, default="UNPAID")

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.employee} - {self.period}"


# 🔥 PURE CALCULATION FUNCTION (CLEAN)
# def calculate_salary_values(salary):
#     config = PayrollConfiguration.objects.first()

#     penalty_rate = config.late_penalty_flat_rate if config else Decimal("500.00")
#     multiplier = Decimal(str(config.overtime_rate_multiplier)) if config else Decimal("1.5")

#     base_pay = salary.hourly_rate_snapshot * Decimal(str(salary.total_hours))
#     overtime_pay = salary.hourly_rate_snapshot * multiplier * Decimal(str(salary.overtime_hours))

#     gross = base_pay + overtime_pay
#     deduction = Decimal(salary.late_instances_count) * penalty_rate
#     net = gross - deduction

#     salary.gross_earnings = gross
#     salary.lateness_deduction = deduction
#     salary.net_pay = net

#     return salary


# # 🔥 MAIN SALARY GENERATOR
# def calculate_monthly_salary(user, year, month):
#     config = PayrollConfiguration.objects.first()
#     penalty_rate = config.late_penalty_flat_rate if config else Decimal("500.00")

    

#     period_date = datetime.date(year, month, 1)
#     period, _ = PayrollPeriod.objects.get_or_create(month=period_date)

#     attendance_qs = Attendance.objects.filter(
#         employee=user,
#         clock_in_time__year=year,
#         clock_in_time__month=month
#     )

#     totals = attendance_qs.aggregate(
#         total_worked=Sum('total_hours'),
#         total_ot=Sum('overtime_hours')
#     )

#     late_count = attendance_qs.filter(status=AttendanceStatus.LATE).count()

#     total_hours = totals['total_worked'] or 0.0
#     total_ot = totals['total_ot'] or 0.0

#     salary, _ = Salary.objects.update_or_create(
#         employee=user,
#         period=period,
#         defaults={
#             'hourly_rate_snapshot': user.hourly_rate,
#             'total_hours': total_hours,
#             'overtime_hours': total_ot,
#             'late_instances_count': late_count,
#         }
#     )

#     # 🔥 Calculate AFTER creation
#     salary = calculate_salary_values(salary)
#     salary.save()

#     return salary



# class PayrollPeriod(models.Model):
#     """Defines the timeframe (e.g., October 2023)"""
#     month = models.DateField(unique=True)
#     is_closed = models.BooleanField(default=False, help_text="Set to true once salaries are paid")

#     def __str__(self):
#         return self.month.strftime('%B %Y')
    

# class PayrollConfiguration(models.Model):
#     """Global rules for calculations"""
#     late_penalty_flat_rate = models.DecimalField(
#         max_digits=10, 
#         decimal_places=2, 
#         default=500.00, 
#         help_text="Amount to deduct per LATE instance (after grace period)"
#     )
#     overtime_rate_multiplier = models.FloatField(
#         default=1.5, 
#         help_text="Multiplier for overtime hours (e.g. 1.5 for time-and-a-half)"
#     )

#     class Meta:
#         verbose_name = "Payroll Configuration"



# class Salary(models.Model):
#     employee = models.ForeignKey(
#         settings.AUTH_USER_MODEL, 
#         on_delete=models.CASCADE, 
#         related_name='salaries',
#         null=True
#     )
#     period = models.ForeignKey(PayrollPeriod, on_delete=models.PROTECT)

#      # --- ATTENDANCE DATA ---
#     # Aggregated Data (from Attendance App)
#     total_hours = models.FloatField(default=0.0)
#     overtime_hours = models.FloatField(default=0.0)
#     late_instances_count = models.IntegerField(default=0, help_text="Count of records with status='LATE'")
    
#     # --- SNAPSHOTS (To keep data accurate if user info changes) ---
#     hourly_rate_snapshot = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     # overtime_rate = models.ForeignKey(EmployeePreRecord, null=True, blank=True)
    
    

#     # --- MATH ---
#     gross_earnings = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
#     lateness_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     net_pay = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
#     is_paid = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

#         # To track the payment in Paystack/Flutterwave
#     transaction_reference = models.CharField(max_length=100, blank=True, null=True)
#     payment_status = models.CharField(max_length=20, default="UNPAID") # PENDING, SUCCESS, FAILED
#     receipt_pdf = models.FileField(upload_to='receipts/', blank=True, null=True)
    


#     def save(self, *args, **kwargs):
#         # 1. Base Pay
#         base_pay = float(self.hourly_rate_snapshot) * self.total_hours
        
#         # 2. Dynamic Overtime calculation
#         # We try to get the multiplier from your Config model
#         # from .models import PayrollConfiguration
#         config = PayrollConfiguration.objects.first()
#         multiplier = config.overtime_rate_multiplier if config else 1.5
        
#         overtime_pay = float(self.hourly_rate_snapshot) * multiplier * self.overtime_hours
        
#         # 3. Final Totals
#         self.gross_earnings = base_pay + overtime_pay
#         self.net_pay = float(self.gross_earnings) - float(self.lateness_deduction)
        
#         super().save(*args, **kwargs)




#     def calculate_monthly_salary(user, year, month):
#         # 1. Get the Rules
#         config = PayrollConfiguration.objects.first()
#         penalty_rate = config.late_penalty_flat_rate if config else 500.00

#         # 2. Get or Create the Payroll Period
#         # This matches the 'period' field in your Salary model
#         period_date = timezone.datetime(year, month, 1).date()
#         period, _ = PayrollPeriod.objects.get_or_create(month=period_date)

#         # 3. Filter attendance for this user for the specific month
#         attendance_qs = Attendance.objects.filter(
#             employee=user,
#             clock_in_time__year=year,
#             clock_in_time__month=month
#         )

#         # 4. Aggregate data
#         totals = attendance_qs.aggregate(
#             total_worked=Sum('total_hours'),
#             total_ot=Sum('overtime_hours')
#         )
#         late_count = attendance_qs.filter(status=AttendanceStatus.LATE).count()

#         # 5. Prepare values
#         total_hours = totals['total_worked'] or 0.0
#         total_ot = totals['total_ot'] or 0.0
#         lateness_deduction = late_count * float(penalty_rate)

#         # 6. Update or Create Salary using the 'period' foreign key
#         salary, created = Salary.objects.update_or_create(
#             employee=user,
#             period=period,  # Fixed: using the foreign key instead of month
#             defaults={
#                 'hourly_rate_snapshot': user.hourly_rate,
#                 'total_hours': total_hours,
#                 'overtime_hours': total_ot,
#                 'late_instances_count': late_count,
#                 'lateness_deduction': lateness_deduction,
#             }
#         )

#         return salary



    # def save(self, *args, **kwargs):
    #     # Math based on your updated Attendance fields
    #     base_pay = float(self.hourly_rate_snapshot) * self.total_hours
        
    #     # You can add logic for overtime multiplier here (e.g., 1.5x)
    #     overtime_pay = float(self.hourly_rate_snapshot) * 1.5 * self.overtime_hours
        
    #     self.gross_earnings = base_pay + overtime_pay
    #     self.net_pay = float(self.gross_earnings) - float(self.lateness_deduction)
        
    #     super().save(*args, **kwargs)

    # class Meta:
    #     unique_together = ('employee', 'period')
           
               
    



# class Department(models.Model):
#     name = models.CharField(max_length=100, null=True)
#     def __str__(self): return self.name

# class JobTitle(models.Model):
#     title = models.CharField(max_length=100, null=True)
#     # department = models.ForeignKey(Department, on_delete=models.CASCADE)
#     def __str__(self): return self.title

# class EmploymentStatus(models.Model):
#     name = models.CharField(max_length=50, null=True)
#     def __str__(self): return self.name


# class EmployeePreRecord(models.Model):
#     employee_id = models.CharField(max_length=20, unique=True, null=True)
#     job_title = models.ForeignKey(JobTitle, on_delete=models.SET_NULL, null=True)
#     department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
#     employment_status = models.ForeignKey(EmploymentStatus, on_delete=models.SET_NULL, null=True, blank=True)
#     hire_date = models.DateField(null=True)
#     contract_end_date = models.DateField(null=True, blank=True,  help_text="Only for contract staff")
#     resignation_date = models.DateField(null=True, blank=True, help_text="Date the employee officially left")
#     # work_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
#     # work_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
#     # allowed_radius = models.IntegerField(default=100, help_text="In meters")
#     is_hr = models.BooleanField(default=False)


#     def __str__(self):
#         return f" ({self.employee_id})"



# # both users and HR uses the page

# class User(AbstractUser): 
#     def save(self, *args, **kwargs):
#         # Only auto-fill if this is a NEW user (no primary key yet)
#         if not self.pk and self.employee_id:
#             try:
#                 # Look up the HR Master List
#                 record = EmployeePreRecord.objects.get(employee_id=self.employee_id)
                
#                 # Automatically pull the data into the User profile
#                 self.department = record.department
#                 self.job_title = record.job_title
#                 self.employment_status = record.employment_status
#                 self.is_hr = record.is_hr
#             except EmployeePreRecord.DoesNotExist:
#                 # Optional: You could raise an error here to prevent signup
#                 raise ValidationError("Employee ID not found in HR records.")
                
        
#         super().save(*args, **kwargs)
#     assigned_workspaces = models.ManyToManyField(
#         'attendance.Workspace', 
#         related_name='employees', 
#         blank=True
#     )
#     employee_id = models.CharField(max_length=20, unique=True, null=True)
#     hr_profile = models.OneToOneField(
#         EmployeePreRecord, 
#         on_delete=models.PROTECT, # Protects HR data from accidental deletion
#         null=True, 
#         blank=True
#     )

#     is_hr = models.BooleanField(null=True)
#     #Personal info
#     full_name = models.CharField(max_length=100, null=True)
#     address = models.TextField(null=True , max_length=100)
#     
#     

    
#     # Payroll Info
#     phone_number = models.CharField( max_length=20, unique=True, null=True)
#     tax_id = models.CharField(max_length=50, unique=True, null=True)
#     bank_account_number = models.CharField( max_length=50, null=True, unique=True)
#     hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    
    

#     def __str__(self):
#         return f"{self.get_full_name()} ({self.employee_id})"
    

   






        




