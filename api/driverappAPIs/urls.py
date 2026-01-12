from django.urls import path
from .view import SignUpView, SignInView, ProfileView

urlpatterns = [
    path('auth/driver/signup/', SignUpView.as_view(), name='signup'),
    path('auth/driver/signin/', SignInView.as_view(), name='signin'),
    path('auth/driver/profile/', ProfileView.as_view(), name='profile'),
]