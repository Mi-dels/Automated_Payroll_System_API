from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import AutoSchema

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ProfileSerializer,
)


class AuthViewSet(viewsets.ViewSet):

   
    # REGISTER
    @extend_schema(auth=[], request=RegisterSerializer)
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "message": "User registered successfully",
            "user_id": user.id
        })


  
    # LOGIN
    @extend_schema(auth=[], request=LoginSerializer)
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data)



    # PROFILE
    @extend_schema(request=ProfileSerializer)
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated]
    )
    def profile(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


    
    # LOGOUT
    
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated]
    )
    def logout(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logged out successfully"})

        except Exception:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )

















































# from django.shortcuts import render
# from rest_framework import status, viewsets
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.decorators import action

# from rest_framework_simplejwt.tokens import RefreshToken

# from .serializers import (
#     RegisterSerializer,
#     LoginSerializer,
#     ProfileSerializer
# )


# class AuthViewSet(viewsets.ViewSet):

#     # =====================================
#     # REGISTER
#     # =====================================
#     @action(detail=False, methods=["post"])
#     def register(self, request):

#         serializer = RegisterSerializer(
#             data=request.data
#         )

#         serializer.is_valid(raise_exception=True)

#         user = serializer.save()

#         return Response({
#             "message": "User registered successfully",
#             "user_id": user.id
#         })


#     # =====================================
#     # LOGIN
#     # =====================================
#     @action(detail=False, methods=["post"])
#     def login(self, request):

#         serializer = LoginSerializer(
#             data=request.data
#         )

#         serializer.is_valid(raise_exception=True)

#         return Response(
#             serializer.validated_data,
#             status=status.HTTP_200_OK
#         )


#     # =====================================
#     # PROFILE
#     # =====================================
#     @action(
#         detail=False,
#         methods=["get"],
#         permission_classes=[IsAuthenticated]
#     )
#     def profile(self, request):

#         serializer = ProfileSerializer(
#             request.user
#         )

#         return Response(serializer.data)


#     # =====================================
#     # LOGOUT
#     # =====================================
#     @action(
#         detail=False,
#         methods=["post"],
#         permission_classes=[IsAuthenticated]
#     )
#     def logout(self, request):

#         try:
#             refresh_token = request.data["refresh"]

#             token = RefreshToken(refresh_token)

#             token.blacklist()

#             return Response({
#                 "message": "Logged out successfully"
#             })

#         except Exception:
#             return Response(
#                 {"error": "Invalid token"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )