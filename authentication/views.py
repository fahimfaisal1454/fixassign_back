# authentication/views.py

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

# Import only what we use (clear & explicit)
from .serializers import (
    UserRegistrationSerializer,
    StaffApproveSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    UserProfileUpdateSerializer,
    AdminCreateUserSerializer,   # <-- make sure this exists in serializers.py
)

User = get_user_model()


# ---------------------------
# Permissions
# ---------------------------
class IsAdmin(BasePermission):
    """
    Admin-only permission (role field must be 'Admin', case-insensitive).
    """
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "role", "").lower() == "admin"
        )


# ---------------------------
# Public Registration (optional if you keep self-signup)
# ---------------------------
class UserRegistrationView(generics.ListCreateAPIView):
    """
    POST: Public registration (e.g., General users).
    GET: Disabled to avoid exposing user list.
    """
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

    def get(self, request, *args, **kwargs):
        raise MethodNotAllowed("GET")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)


# ---------------------------
# Staff list / create (existing)
# ---------------------------
class StaffListCreateView(generics.ListCreateAPIView):
    """
    GET: List users with optional filters (?approved=true|false, ?role=Teacher).
    POST: Create staff (admin-only).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StaffApproveSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        approved = self.request.query_params.get("approved")
        role = self.request.query_params.get("role")

        if approved is not None:
            approved_bool = str(approved).lower() in ("1", "true", "yes", "y")
            # Using is_approved only if your model has it
            if hasattr(User, "is_approved"):
                qs = qs.filter(is_approved=approved_bool)

        if role:
            qs = qs.filter(role__iexact=role)

        order_field = "date_joined" if hasattr(User, "date_joined") else "id"
        return qs.order_by(f"-{order_field}")

    def create(self, request, *args, **kwargs):
        if not IsAdmin().has_permission(request, self):
            return Response({"detail": "Only admins can create staff."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)


class StaffApproveView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET / PUT/PATCH / DELETE single user (admin-only).
    PUT/PATCH: e.g. {"is_approved": true, "role": "Teacher"}
    """
    permission_classes = [IsAdmin]
    queryset = User.objects.all()
    serializer_class = StaffApproveSerializer

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data.copy()

        # Normalize "is_approved" if it exists in your model/serializer
        if "is_approved" in data:
            is_approved = data.get("is_approved")
            if isinstance(is_approved, str):
                is_approved = is_approved.lower() == "true"
            data["is_approved"] = is_approved

        try:
            serializer = self.get_serializer(user, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {"message": f"User {user.username} updated successfully.", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        except IntegrityError:
            return Response({"error": "Database integrity error."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        username = user.username
        user.delete()
        return Response({"message": f"User {username} deleted successfully."}, status=status.HTTP_200_OK)


# ---------------------------
# JWT Token (login)
# ---------------------------
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# ---------------------------
# Profile & Password
# ---------------------------
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # IMPORTANT: pass request in context so serializer can build absolute URLs
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # allow file uploads (profile_picture)

    def patch(self, request, *args, **kwargs):
        user = request.user
        ser = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            # Return the latest merged profile (with absolute photo URL + teacher fallbacks)
            out = UserProfileSerializer(user, context={'request': request})
            return Response(out.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------
# Admin-only: Users CRUD + Reset Password
# ---------------------------
class AdminUserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/admin/users/?role=Teacher&q=ali
    POST /api/admin/users/  { username, email, role, phone, [password], ... }
         - Password is hashed; if omitted, server generates a temp one and returns it once.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminCreateUserSerializer

    def get_queryset(self):
        qs = User.objects.all().order_by("-id")
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role__iexact=role)
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(username__icontains=q)
        return qs

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = ser.save()
        data = AdminCreateUserSerializer(user).data
        # Show the temp password once (if generated server-side)
        data["temp_password"] = ser.context.get("temp_password")
        return Response(data, status=status.HTTP_201_CREATED)


class AdminUserRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/admin/users/<id>/
    PATCH /api/admin/users/<id>/  (e.g., {"role":"Teacher","is_active":true})
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = User.objects.all()
    serializer_class = StaffApproveSerializer  # reuse for updates


class AdminResetPasswordView(generics.UpdateAPIView):
    """
    PATCH /api/admin/users/<id>/reset-password/  {"new_password":"..."}
    If new_password is omitted, generates a random one and returns it.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = User.objects.all()

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        new_pw = request.data.get("new_password")
        if not new_pw:
            import secrets
            new_pw = secrets.token_urlsafe(8)
        user.set_password(new_pw)            # <-- hashed
        user.must_change_password = True
        user.save()
        return Response({"message": "Password reset.", "temp_password": new_pw}, status=status.HTTP_200_OK)
