# payroll/serializers.py
from rest_framework import serializers, permissions, viewsets
from .models import User, EmployeePreRecord, Department, JobTitle, EmploymentStatus

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

# 3. THE STAFF SERIALIZER (The one you sent - handles Auto-fill & Locking)
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'employee_id', 'department', 'job_title', 'employment_status', 'is_hr', 'password']
#         extra_kwargs = {'password': {'write_only': True}}

#     def create(self, validated_data):
#         emp_id = validated_data.get('employee_id')
#         try:
#             hr_record = EmployeePreRecord.objects.get(employee_id=emp_id)
#             validated_data['department.name'] = hr_record.department
#             validated_data['job_title.name'] = hr_record.job_title
#             validated_data['employment_status.name'] = hr_record.employment_status
#             validated_data['is_hr'] = hr_record.is_hr
#         except EmployeePreRecord.DoesNotExist:
#             raise serializers.ValidationError({"employee_id": "That ID doesn't exist in our HR records."})
#         return super().create(validated_data)

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

    def create(self, validated_data):
        emp_id = validated_data.get('employee_id')
        try:
            # Connect the user to their official HR data using the ID
            hr_data = EmployeePreRecord.objects.get(employee_id=emp_id)
            validated_data['hr_profile'] = hr_data
            validated_data['is_hr'] = hr_data.is_hr
        except EmployeePreRecord.DoesNotExist:
            raise serializers.ValidationError({"employee_id": "Invalid ID."})
            
        return super().create(validated_data)


    def update(self, instance, validated_data):
        request_user = self.context['request'].user
        if not request_user.is_hr:
            protected_fields = ['employee_id', 'department', 'job_title', 'employment_status', 'is_hr']
            for field in protected_fields:
                validated_data.pop(field, None)
        return super().update(instance, validated_data)
    





from payroll.models import PayrollPeriod
from django.contrib.auth import get_user_model

User = get_user_model()


class HRPayrollActionSerializer(serializers.Serializer):

    ACTION_CHOICES = (
        ("generate_payslip", "Generate Payslip"),
        ("send_email", "Send Payslip Email"),
        ("bulk_export", "Bulk Export"),
    )

    action = serializers.ChoiceField(choices=ACTION_CHOICES)

    # HR-friendly input (NOT IDs)
    employee_email = serializers.EmailField(required=False)
    employee_name = serializers.CharField(required=False)

    month = serializers.DateField(required=True)  # e.g. 2026-04-01

    format = serializers.ChoiceField(
        choices=(("pdf", "PDF"), ("json", "JSON")),
        default="pdf"
    )

    def validate(self, data):
        action = data["action"]

        # ---------------- PERIOD RESOLUTION ----------------
        period, _ = PayrollPeriod.objects.get_or_create(
            month=data["month"]
        )
        data["period"] = period

        # ---------------- EMPLOYEE RESOLUTION ----------------
        email = data.get("employee_email")
        name = data.get("employee_name")

        if action in ["generate_payslip", "send_email"]:

            if not email and not name:
                raise serializers.ValidationError(
                    "Provide employee_email or employee_name"
                )

            try:
                if email:
                    user = User.objects.get(email=email)
                else:
                    user = User.objects.get(username=name)

            except User.DoesNotExist:
                raise serializers.ValidationError("Employee not found")

            data["employee"] = user

        return data


from rest_framework import serializers

from payroll.models import Salary, PayrollPeriod


class SalaryApprovalSerializer(serializers.Serializer):

    salary_id = serializers.IntegerField()


class SalaryPaymentSerializer(serializers.Serializer):

    salary_id = serializers.IntegerField()

    transaction_reference = serializers.CharField(
        required=False
    )


class BulkPaymentSerializer(serializers.Serializer):

    period_id = serializers.IntegerField()

    transaction_prefix = serializers.CharField(
        required=False,
        default="BULK"
    )










# # serializers.py
# class EmployeePreRecordSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EmployeePreRecord
#         fields = '__all__'



# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'employee_id', 'department', 'job_title', 'employment_status', 'is_hr', 'password']
#         extra_kwargs = {'password': {'write_only': True}}

#     def create(self, validated_data):
#         emp_id = validated_data.get('employee_id')

#         # 1. Look up the HR-filled data
#         try:
#             hr_record = EmployeePreRecord.objects.get(employee_id=emp_id)
#             # 2. Force these fields to match the HR record
#             validated_data['department.name'] = hr_record.department
#             validated_data['job_title.title'] = hr_record.job_title
#             validated_data['employment_status.name'] = hr_record.employment_status
#             validated_data['is_hr'] = hr_record.is_hr
#         except EmployeePreRecord.DoesNotExist:
#             raise serializers.ValidationError({"employee_id": "That ID doesn't exist in our HR records."})

#         return super().create(validated_data)

#     def update(self, instance, validated_data):
#         request_user = self.context['request'].user
        
#         # 3. Security: If the user is NOT HR, remove protected fields from the update
#         if not request_user.is_hr:
#             protected_fields = ['employee_id', 'department', 'job_title', 'employment_status', 'is_hr']
#             for field in protected_fields:
#                 validated_data.pop(field, None) # Silently ignore changes to these fields
        
#         return super().update(instance, validated_data)



# class EmployeePreRecordSerializer(serializers.ModelSerializer):


# class UserSerializer(serializers.ModelSerializer):
#     # We "pull in" the string names of these foreign keys 
#     # so the frontend sees "IT" instead of just an ID number like "1"
#     department_name = serializers.ReadOnlyField(source='department.name')
#     job_title_name = serializers.ReadOnlyField(source='job_title.title')
#     status_name = serializers.ReadOnlyField(source='employment_status.name')

#     class Meta:
#         model = User
#         # List the fields you want to send to the frontend
#         fields = [
#             'id', 'username', 'first_name', 'last_name', 'email',
#             'employee_id', 'phone_number', 'department', 'department_name',
#             'job_title', 'job_title_name', 'employment_status', 'status_name',
#             'hire_date', 'is_hr'
#         ]
#         # We don't want to send the password back to the frontend!
#         extra_kwargs = {'password': {'write_only': True}}

#         # payroll/urls.py
#         def to_representation(self, instance):
#             data = super().to_representation(instance)
#             request = self.context.get('request')

#         # If the person looking at the data is NOT an HR user...
#             if request and request.user.is_authenticated and not request.user.is_hr:
#             # ...hide sensitive payroll info
#                 sensitive_fields = ['bank_account_number', 'tax_id', 'is_hr']
#             for field in sensitive_fields:
#                 data.pop(field, None)
        
#             return data


       
