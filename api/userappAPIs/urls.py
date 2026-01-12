from django.urls import path
<<<<<<< HEAD
from .views import CustomerSignUpView, SignInView, ProfileView, UserSearchAPIView

urlpatterns = [
    path('auth/signup/customer', CustomerSignUpView.as_view(), name='signup'),
    path('auth/signin/customer', SignInView.as_view(), name='signin'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path("user/search/", UserSearchAPIView.as_view(), name="user-search"),
=======
from .views import SignInView, ProfileView, CustomerSignUpView, ProfileUpdateView

urlpatterns = [
    path('auth/signup/customer/', CustomerSignUpView.as_view(), name='signup'),
    path('auth/signin/customer/', SignInView.as_view(), name='signin'),
    path('auth/profile/customer/', ProfileView.as_view(), name='profile'),
    path('auth/profile/update/', ProfileUpdateView.as_view(), name='profile'),
>>>>>>> e6649f20f2fb4261e0b8e9b99629d566b40325fa
]