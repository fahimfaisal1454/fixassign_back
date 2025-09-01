from django.urls import path
from .views import*
from django.contrib.auth import views as auth_views
from django.conf import settings


urlpatterns = [

    path('register/',UserRegistrationView.as_view(),name='register'),
    path('approve_staff/', StaffListCreateView.as_view(), name='approve_staff'),
    path('approve_staff/<int:pk>/', StaffApproveView.as_view(), name='approve-staff'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('user/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('update-profile/', UserProfileUpdateView.as_view(), name='update-profile'),

]