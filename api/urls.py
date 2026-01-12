from django.urls import path, include
from .views import SignUpView, SignInView, ProfileView

urlpatterns = [
    path('auth/signup/', SignUpView.as_view(), name='signup'),
    path('auth/signin/', SignInView.as_view(), name='signin'),
    path('profile/', ProfileView.as_view(), name='profile'),
<<<<<<< HEAD
    path('', include('api.userappAPIs.urls')),

=======
    path('', include('api.driverappAPIs.urls')),
    path('', include('api.userappAPIs.urls')),
>>>>>>> e6649f20f2fb4261e0b8e9b99629d566b40325fa
]