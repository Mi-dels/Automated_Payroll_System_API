# payroll/serializers.py
from rest_framework import serializers, permissions
from .models import User, EmployeePreRecord, Department, JobTitle, EmploymentStatus
from payroll.models import PayrollPeriod, PayrollConfiguration, Salary
from django.contrib.auth import get_user_model




User = get_user_model()


# 1. THE LOOKUP SERIALIZERS (Allows HR to "Add New")
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']

class JobTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobTitle
        fields = ['id', 'title']


class EmploymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentStatus
        fields = ['id', 'name']


# 2. THE HR SERIALIZER (Used for HR Pre-Records)
class EmployeePreRecordSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer() # Allows nested "Add New"
    job_title = JobTitleSerializer()
    employment_status = EmploymentStatusSerializer()
    
    class Meta:
        model = EmployeePreRecord
        fields = '__all__'

    def create(self, validated_data):
        dept_data = validated_data.pop('department')
        job_data = validated_data.pop('job_title') 
        status_data = validated_data.pop('employment_status')
        
        dept, _ = Department.objects.get_or_create(**dept_data)
        job, _ = JobTitle.objects.get_or_create(**job_data)
        status, _ = EmploymentStatus.objects.get_or_create(**status_data)
        
       
        return EmployeePreRecord.objects.create(department=dept, job_title=job, employment_status=status, **validated_data)



class UserSerializer(serializers.ModelSerializer):
    # These "pull" the data from the linked HR record for display only
    department = serializers.CharField(source='hr_profile.department.name', read_only=True)
    job_title = serializers.CharField(source='hr_profile.job_title.title', read_only=True)
    employment_status = serializers.CharField(source='hr_profile.employment_status.name', read_only=True)
    is_hr = serializers.BooleanField(source='hr_profile.is_hr',read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'employee_id', 
            'department', 'job_title', 'employment_status', 'is_hr',# Official HR data (Read-only)
            'phone_number', 'address', 'password', 'emergency_contact', 'date_of_birth', 
              'bank_account_number' , 'bank_code'   # Personal data (Editable)
        ]
        extra_kwargs = {'password': {'write_only': True}}


    def validate_employee_id(self, value):
        if not value:
            return value
        if not EmployeePreRecord.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError(
                "This employee ID does not exist in HR records"
            )
        request = self.context.get('request')
        if request and User.objects.filter(employee_id=value).exclude(id=request.user.id).exists():
            raise serializers.ValidationError(
                "This employee ID is already taken"
            )
        return value

    # def create(self, validated_data):
    #     emp_id = validated_data.get('employee_id')
    #     try:
    #         # Connect the user to their official HR data using the ID
    #         hr_data = EmployeePreRecord.objects.get(employee_id=emp_id)
    #         validated_data['hr_profile'] = hr_data
    #         validated_data['is_hr'] = hr_data.is_hr
    #     except EmployeePreRecord.DoesNotExist:
    #         raise serializers.ValidationError({"employee_id": "Invalid ID."})
            
    #     return super().create(validated_data)


    def update(self, instance, validated_data):
        request_user = self.context['request'].user

        password = validated_data.pop('password', None)
        if password:
            from django.contrib.auth.hashers import check_password
        if not check_password(password, instance.password):
            instance.set_password(password)

        if not request_user.is_hr:
            protected_fields = ['employee_id', 'department', 'job_title', 'employment_status', 'is_hr']
            for field in protected_fields:
                validated_data.pop(field, None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
        # return super().update(instance, validated_data)
    



class PayrollPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriod
        fields = ["id", "month", "is_closed"]


class PayrollConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollConfiguration
        fields = ["id", "default_hourly_rate", "default_late_penalty_per_minute", "default_overtime_rate_multiplier"]




class HRPayrollActionSerializer(serializers.Serializer):

    employee_id = serializers.IntegerField()
    year = serializers.IntegerField()
    month = serializers.IntegerField()

    


    # ACTION_CHOICES = (
    #     ("generate_payslip", "Generate Payslip"),
    #     ("send_email", "Send Payslip Email"),
    #     ("bulk_export", "Bulk Export"),
    # )

    # action = serializers.ChoiceField(choices=ACTION_CHOICES)

    # # HR-friendly input (NOT IDs)
    # employee_email = serializers.EmailField(required=False)
    # employee_name = serializers.CharField(required=False)

    # month = serializers.DateField(required=True)  # e.g. 2026-04-01

    # format = serializers.ChoiceField(
    #     choices=(("pdf", "PDF"), ("json", "JSON")),
    #     default="pdf"
    # )

    # def validate(self, data):
    #     action = data["action"]

    #     # ---------------- PERIOD RESOLUTION ----------------
    #     period, _ = PayrollPeriod.objects.get_or_create(
    #         month=data["month"]
    #     )
    #     data["period"] = period

    #     # ---------------- EMPLOYEE RESOLUTION ----------------
    #     email = data.get("employee_email")
    #     name = data.get("employee_name")

    #     if action in ["generate_payslip", "send_email"]:

    #         if not email and not name:
    #             raise serializers.ValidationError(
    #                 "Provide employee_email or employee_name"
    #             )

    #         try:
    #             if email:
    #                 user = User.objects.get(email=email)
    #             else:
    #                 user = User.objects.get(username=name)

    #         except User.DoesNotExist:
    #             raise serializers.ValidationError("Employee not found")

    #         data["employee"] = user

    #     return data





class SalaryApprovalSerializer(serializers.Serializer):

    salary_id = serializers.IntegerField()


class SalaryPaymentSerializer(serializers.Serializer):

    salary_id = serializers.IntegerField()

    transaction_reference = serializers.CharField(
        required=False
    )


class BulkPaymentSerializer(serializers.Serializer):

    period_id = serializers.IntegerField()

    # transaction_prefix = serializers.CharField(
    #     required=False,
    #     default="BULK"
    # )










