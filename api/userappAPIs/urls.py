from django.urls import path
from .views import CustomerSignUpView, SignInView, ProfileView, UserSearchAPIView

urlpatterns = [
    path('auth/signup/customer', CustomerSignUpView.as_view(), name='signup'),
    path('auth/signin/customer', SignInView.as_view(), name='signin'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path("user/search/", UserSearchAPIView.as_view(), name="user-search"),
]