from django.urls import path
from .view import SignUpView, SignInView, ProfileView
from .delivery import DeliveryStatusView

urlpatterns = [
    path('auth/signup/driver/', SignUpView.as_view(), name='signup'),
    path('auth/signin/driver/', SignInView.as_view(), name='signin'),
    path('auth/profile/driver/', ProfileView.as_view(), name='profile'),
    path('deliveries/', DeliveryStatusView.as_view(), name='delivery-status'),

]