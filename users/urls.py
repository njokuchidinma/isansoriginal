from django.urls import path
from .views import UserRegistration, AdminLoginView, LoginView, LogoutView, ForgotPasswordView, ChangePassword, UserProfile



urlpatterns = [
    path('register/', UserRegistration.as_view(), name='user-registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('change-password/', ChangePassword.as_view(), name='change-password'),
    path('profile/', UserProfile.as_view(), name='user-profile'),
]