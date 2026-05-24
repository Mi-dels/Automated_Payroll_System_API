from decimal import Decimal
from django.db.models import Sum
from attendance.models import Shift as ShiftModel
from attendance.models import Attendance
from payroll.models import Salary, PayrollPeriod, PayrollConfiguration
from attendance.services.absence import calculate_absent_days
import datetime


def generate_salary(user, year, month):

    # CONFIG CHECK
    
    config = PayrollConfiguration.objects.first()
    if not config:
        raise Exception("Payroll configuration not set. Please create one first.")

    
    # PERIOD CHECK
    
    period = PayrollPeriod.objects.filter(
        month__year=year,
        month__month=month
    ).first()

    if not period:
        raise Exception("Payroll period not found. Please create one first.")

    
    # ATTENDANCE FETCH
    
    attendances = Attendance.objects.filter(
        employee=user,
        clock_in_time__year=year,
        clock_in_time__month=month,
        clock_out_time__isnull=False
    )

    if not attendances.exists():
        return {
            "message": "No attendance found",
            "net_pay": 0
        }

    
    # GET EMPLOYEE'S SHIFT

    shift_id = attendances.filter(
        shift__isnull=False
    ).values_list('shift', flat=True).first()

    shift_obj = ShiftModel.objects.filter(id=shift_id).first() if shift_id else None

    # RESOLVE RATES
    #(shift overrides config defaults)

    hourly_rate = (
        shift_obj.hourly_rate
        if shift_obj and shift_obj.hourly_rate
        else config.default_hourly_rate
    )

    late_penalty_per_minute = (
        shift_obj.late_penalty_per_minute
        if shift_obj and shift_obj.late_penalty_per_minute
        else config.default_late_penalty_per_minute
    )
    
    overtime_multiplier = (
        Decimal(str(shift_obj.overtime_rate_multiplier))
        if shift_obj and shift_obj.overtime_rate_multiplier
        else Decimal(str(config.default_overtime_rate_multiplier))
    )


    # AUTO ABSENT PENALTY
    #(hourly_rate * shift duration)

    if shift_obj:
        shift_start = datetime.datetime.combine(
            datetime.date.today(), shift_obj.start_time
        )
        shift_end = datetime.datetime.combine(
            datetime.date.today(), shift_obj.end_time
        )

        # Handles night time

        if shift_obj.end_time < shift_obj.start_time:
            shift_end += datetime.timedelta(days=1)
        shift_hours = float(
            (shift_end - shift_start).total_seconds() / 3600
        )
    else:
        shift_hours = Decimal("8") # default 8 hours
    
    absent_penalty = hourly_rate * Decimal(str(shift_hours))

    
    # SAFE AGGREGATION
    
    totals = attendances.aggregate(
        total_overtime=Sum("overtime_hours"),
        total_late=Sum("late_minutes")
    )

    total_hours = sum(
        a.total_hours or 0 for a in attendances
    )

    total_overtime = totals.get("total_overtime") or 0
    total_late = totals.get("total_late") or 0

    
    # ABSENCE LOGIC
    
    absence_data = calculate_absent_days(user, year, month)
    absent_days = absence_data.get("absent_days", 0)

   

    
    # CALCULATIONS
    
    base_salary = Decimal(str(total_hours)) * hourly_rate

    overtime_pay = (
        Decimal(str(total_overtime))
        * hourly_rate
        * overtime_multiplier
    )

    late_deduction = min(
        Decimal(str(total_late)) * late_penalty_per_minute,
        
    )

    absence_deduction = Decimal(absent_days) * absent_penalty

    gross_salary = base_salary + overtime_pay

    net_salary = max(
        Decimal("0.00"),
        gross_salary - late_deduction - absence_deduction
    )

    
    # SAVE OR UPDATE SALARY
    
    salary, created = Salary.objects.get_or_create(
        employee=user,
        period=period,
        defaults={
            "total_hours": total_hours,
            "overtime_hours": total_overtime,
            "late_instances_count": total_late,
            "hourly_rate_snapshot": hourly_rate,
            "gross_earnings": gross_salary,
            "lateness_deduction": late_deduction,
            "net_pay": net_salary
        }
    )

    if not created:
        salary.total_hours = total_hours
        salary.overtime_hours = total_overtime
        salary.late_instances_count = total_late
        salary.hourly_rate_snapshot = hourly_rate
        salary.gross_earnings = gross_salary
        salary.lateness_deduction = late_deduction
        salary.net_pay = net_salary
        salary.save()

    
    # RESPONSE
    
    return {
        "employee": user.id,
        "period": str(period),
        "shift":shift_obj.name if shift_obj else "Default",
        "hourly_rate": float(hourly_rate),
        "shift_hours": round(shift_hours),
        "absent_penalty_per_day": float(absent_penalty),
        "total_hours": round(float(total_hours), 2),
        "overtime_hours": float(total_overtime),
        "absent_days": absent_days,
        "late_minutes": total_late,
        "gross_pay": float(gross_salary),
        "late_deduction": float(late_deduction),
        "absense_deduction": float(absence_deduction),
        "net_pay": round(float(net_salary), 2)
    }
















# from decimal import Decimal
# from django.db.models import Sum

# from attendance.models import Attendance
# from payroll.models import Salary, PayrollPeriod, PayrollConfiguration

# from attendance.services.absence import calculate_absent_days


# def generate_salary(user, year, month):

#     config = PayrollConfiguration.objects.first()

#     if not config:
#         raise Exception("Payroll configuration not set")

#     period = PayrollPeriod.objects.filter(
#         month__year=year,
#         month__month=month
#     ).first()

#     if not period:
#         raise Exception("Payroll period not found")

#     attendances = Attendance.objects.filter(
#         employee=user,
#         clock_in_time__year=year,
#         clock_in_time__month=month,
#         clock_out_time__isnull=False
#     )

#     if not attendances.exists():
#         return {
#             "message": "No attendance found",
#             "net_pay": 0
#         }

#     # -------------------------
#     # ATTENDANCE TOTALS
#     # -------------------------
#     totals = attendances.aggregate(
#         total_overtime=Sum("overtime_hours"),
#         total_late=Sum("late_minutes")
#     )

#     total_hours = sum(
#         a.total_hours for a in attendances
#     )

#     total_overtime = totals["total_overtime"] or 0
#     total_late = totals["total_late"] or 0

#     # -------------------------
#     # ABSENCE CALCULATION
#     # -------------------------
#     absence_data = calculate_absent_days(user, year, month)

#     absent_days = absence_data["absent_days"]

#     # -------------------------
#     # CONSTANTS
#     # -------------------------
#     HOURLY_RATE = Decimal("2000")
#     ABSENT_PENALTY = Decimal("2000")

#     # -------------------------
#     # SALARY CALCULATION
#     # -------------------------
#     base_salary = Decimal(str(total_hours)) * HOURLY_RATE

#     overtime_pay = (
#         Decimal(str(total_overtime))
#         * HOURLY_RATE
#         * Decimal(str(config.overtime_rate_multiplier))
#     )

#     late_deduction = min(
#         Decimal(str(total_late)) * config.late_penalty_flat_rate,
#         Decimal("5000")
#     )

#     absence_deduction = Decimal(absent_days) * ABSENT_PENALTY

#     gross_salary = base_salary + overtime_pay

#     net_salary = max(
#         Decimal("0.00"),
#         gross_salary - late_deduction - absence_deduction
#     )

#     # -------------------------
#     # SAVE SALARY
#     # -------------------------
#     salary, created = Salary.objects.get_or_create(
#         employee=user,
#         period=period,
#         defaults={
#             "total_hours": total_hours,
#             "overtime_hours": total_overtime,
#             "late_instances_count": total_late,
#             "hourly_rate_snapshot": HOURLY_RATE,
#             "gross_earnings": gross_salary,
#             "lateness_deduction": late_deduction,
#             "net_pay": net_salary
#         }
#     )

#     if not created:
#         salary.total_hours = total_hours
#         salary.overtime_hours = total_overtime
#         salary.late_instances_count = total_late
#         salary.hourly_rate_snapshot = HOURLY_RATE
#         salary.gross_earnings = gross_salary
#         salary.lateness_deduction = late_deduction
#         salary.net_pay = net_salary
#         salary.save()

#     return {
#         "employee": user.id,
#         "period": str(period),
#         "total_hours": float(total_hours),
#         "overtime_hours": float(total_overtime),
#         "absent_days": absent_days,
#         "gross_pay": float(gross_salary),
#         "net_pay": float(net_salary)
#     }








