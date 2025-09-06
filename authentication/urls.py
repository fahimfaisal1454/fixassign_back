from django.urls import path
from .views import (
    UserRegistrationView,
    StaffListCreateView,
    StaffApproveView,
    CustomTokenObtainPairView,
    UserProfileView,
    PasswordChangeView,
    UserProfileUpdateView,
    AdminUserListCreateView,
    AdminUserRetrieveUpdateView,
    AdminResetPasswordView,
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('user/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('update-profile/', UserProfileUpdateView.as_view(), name='update-profile'),



    # NEW: Admin-only user management
    path('admin/users/', AdminUserListCreateView.as_view(), name='admin-user-list-create'),
    path('admin/users/<int:pk>/', AdminUserRetrieveUpdateView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:pk>/reset-password/', AdminResetPasswordView.as_view(), name='admin-user-reset-password'),
]
