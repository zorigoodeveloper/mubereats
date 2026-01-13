from django.urls import path
from .view import SignUpView, SignInView, ProfileView, AvailableOrdersView, MyOrdersView , DeliveryStatusView

urlpatterns = [
    path('auth/driver/signup/', SignUpView.as_view(), name='signup'),
    path('auth/driver/signin/', SignInView.as_view(), name='signin'),
    path('auth/driver/profile/', ProfileView.as_view(), name='profile'),
    path("driver/orders/available", AvailableOrdersView.as_view()),
    path("driver/orders/my", MyOrdersView.as_view()),
    path("driver/orders/delivery_status", DeliveryStatusView.as_view()),
]   