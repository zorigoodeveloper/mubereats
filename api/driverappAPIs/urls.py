from django.urls import path
from .view import SignUpView, SignInView, ProfileView, AvailableOrdersView, MyOrdersView, AcceptOrderView, UpdateDeliveryStatusView

urlpatterns = [
    path('auth/driver/signup/', SignUpView.as_view(), name='signup'),
    path('auth/driver/signin/', SignInView.as_view(), name='signin'),
    path('auth/driver/profile/', ProfileView.as_view(), name='profile'),
    path("auth/driver/orders/available", AvailableOrdersView.as_view()),
    path("auth/driver/orders/my", MyOrdersView.as_view()),
    path("auth/driver/orders/<int:order_id>/accept", AcceptOrderView.as_view()),
    path("auth/driver/orders/<int:order_id>/delivered", UpdateDeliveryStatusView.as_view()),
]   