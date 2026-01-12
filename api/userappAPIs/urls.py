from django.urls import path
from .views import SignInView, ProfileView, CustomerSignUpView, ProfileUpdateView

urlpatterns = [
    path('auth/signup/customer/', CustomerSignUpView.as_view(), name='signup'),
    path('auth/signin/customer/', SignInView.as_view(), name='signin'),
    path('auth/profile/customer/', ProfileView.as_view(), name='profile'),
    path('auth/profile/update/', ProfileUpdateView.as_view(), name='profile'),
]