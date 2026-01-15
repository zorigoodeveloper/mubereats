from django.urls import path
from .views import (
    AdminUserListView,
    AdminUserDetailView,
    AdminUserUpdateView,
    AdminUserDeleteView,
    AdminSignInView, AdminApproveRestaurantView, AdminApproveDriverView, AdminRestaurantListView, AdminDriverListView,AdminPendingDriverListView, AdminPendingRestaurantListView
)

urlpatterns = [
    path('admin/users/', AdminUserListView.as_view()),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view()),
    path('admin/users/<int:user_id>/update/', AdminUserUpdateView.as_view()),
    path('admin/users/<int:user_id>/delete/', AdminUserDeleteView.as_view()),
    path('admin/login/', AdminSignInView.as_view()),

    path('admin/approve/restaurant/<int:resID>/', AdminApproveRestaurantView.as_view(), name='admin-approve-restaurant'),

    # Жолооч
    path('admin/approve/driver/<int:workerID>/', AdminApproveDriverView.as_view(), name='admin-approve-driver'),
    path('admin/restaurants/', AdminRestaurantListView.as_view(), name='admin-restaurants'),
    path('admin/drivers/', AdminDriverListView.as_view(), name='admin-drivers'),
    path('admin/restaurants/pending/', AdminPendingRestaurantListView.as_view(), name='admin-pending-restaurants'),
    path('admin/drivers/pending/', AdminPendingDriverListView.as_view(), name='admin-pending-drivers'),

]