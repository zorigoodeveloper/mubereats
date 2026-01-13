from django.urls import path
from .view import SignUpView, SignInView, ProfileView, AvailableOrdersView, MyOrdersView , DeliveryView, UpdateDeliveryStatusView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path("orders/available", AvailableOrdersView.as_view()),
    path("orders/my", MyOrdersView.as_view()),
    path("orders/delivery", DeliveryView.as_view()),
    path("orders/delivery_status", UpdateDeliveryStatusView.as_view()),
]   
