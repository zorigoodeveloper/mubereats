from django.urls import path
from .views import SignUpView, SignInView, ProfileView, CustomerSignUpView

urlpatterns = [
    path('auth/signup/customer', CustomerSignUpView.as_view(), name='signup'),
    path('auth/signin/customer', SignInView.as_view(), name='signin'),
    path('profile/', ProfileView.as_view(), name='profile'),
]