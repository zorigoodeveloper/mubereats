from django.urls import path
from .view import SignUpView, SignInView, ProfileView

urlpatterns = [
    path('auth/signup/driver/', SignUpView.as_view(), name='signup'),
    path('auth/signin/driver/', SignInView.as_view(), name='signin'),
    path('profile/', ProfileView.as_view(), name='profile'),
]