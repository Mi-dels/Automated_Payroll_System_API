from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()



# REGISTER

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "email",
            # "employee_id",
            "full_name",
            "phone_number",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user



# LOGIN

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = User.objects.filter(username=data["username"]).first
        # user = authenticate(
        #     username=data["username"],
        #     password=data["password"]
        # )
        # user = User.objects.filter(username=data["username"]).first()

        if not user :
            raise serializers.ValidationError(f"user not found{data['username']}")
        if not user.check_password(data["password"]):
            raise serializers.ValidationError(f"wrong password for user:{datd['username']}")

        refresh = RefreshToken.for_user(user)

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_hr": user.is_hr,
                "employee_id": user.employee_id,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }



# PROFILE

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["password", "groups", "user_permissions"]


























# from django.contrib.auth import authenticate
# from rest_framework import serializers
# from rest_framework_simplejwt.tokens import RefreshToken

# from payroll.models import User


# # =========================================
# # REGISTER
# # =========================================
# class RegisterSerializer(serializers.ModelSerializer):

#     password = serializers.CharField(write_only=True)

#     class Meta:
#         model = User

#         fields = [
#             "username",
#             "password",
#             "email",
#             "employee_id",
#             "full_name",
#             "phone_number"
#         ]

#     def create(self, validated_data):

#         password = validated_data.pop("password")

#         user = User(**validated_data)

#         user.set_password(password)

#         user.save()

#         return user


# # =========================================
# # LOGIN
# # =========================================
# class LoginSerializer(serializers.Serializer):

#     username = serializers.CharField()

#     password = serializers.CharField(write_only=True)

#     def validate(self, data):

#         user = authenticate(
#             username=data["username"],
#             password=data["password"]
#         )

#         if not user:
#             raise serializers.ValidationError(
#                 "Invalid credentials"
#             )

#         refresh = RefreshToken.for_user(user)

#         return {
#             "user": {
#                 "id": user.id,
#                 "username": user.username,
#                 "email": user.email,
#                 "role": user.role,
#                 "is_hr": user.is_hr,
#                 "employee_id": user.employee_id,
#             },

#             "tokens": {
#                 "refresh": str(refresh),
#                 "access": str(refresh.access_token)
#             }
#         }


# # =========================================
# # PROFILE
# # =========================================
# class ProfileSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = User

#         exclude = [
#             "password",
#             "groups",
#             "user_permissions"
#         ]