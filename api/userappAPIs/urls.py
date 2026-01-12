from django.urls import path
from .views import CustomerSignUpView, SignInView, ProfileView, UserSearchAPIView, ProfileUpdateView

urlpatterns = [
    path('auth/signup/customer/', CustomerSignUpView.as_view(), name='signup'),
    path('auth/signin/customer/', SignInView.as_view(), name='signin'),
    path("user/search/", UserSearchAPIView.as_view(), name="user-search"),
    path('auth/profile/customer/', ProfileView.as_view(), name='profile'),
    path('auth/profile/update/customer/', ProfileUpdateView.as_view(), name='profile'),
]