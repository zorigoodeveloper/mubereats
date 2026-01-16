from django.urls import path
from .views import (
    AdminUserListView,
    AdminUserDetailView,
    AdminUserUpdateView,
    AdminUserDeleteView,
    AdminSignInView, AdminApproveRestaurantView, 
    AdminRestaurantListView, 
    AdminPendingRestaurantListView, CouponListView, CouponDetailView, CouponCreateView,
    CouponUpdateView, CouponDeleteView, AdminStatisticsView, AdminPendingWorkersView,
    AdminApproveWorkerView, AdminRejectWorkerView
)

urlpatterns = [
    path('admin/users/', AdminUserListView.as_view()),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view()),
    path('admin/users/<int:user_id>/update/', AdminUserUpdateView.as_view()),
    path('admin/users/<int:user_id>/delete/', AdminUserDeleteView.as_view()),
    path('admin/login/', AdminSignInView.as_view()),

    path('admin/approve/restaurant/<int:resID>/', AdminApproveRestaurantView.as_view(), name='admin-approve-restaurant'),
    
    path('admin/restaurants/', AdminRestaurantListView.as_view(), name='admin-restaurants'),
    path('admin/restaurants/pending/', AdminPendingRestaurantListView.as_view(), name='admin-pending-restaurants'),
    # -----------------------------------------------------------
    path('admin/coupons/', CouponListView.as_view(), name='coupon-list'),
    path('admin/coupons/<int:coupon_id>/', CouponDetailView.as_view(), name='coupon-detail'),
    path('admin/coupons/create/', CouponCreateView.as_view(), name='coupon-create'),
    path('admin/coupons/<int:coupon_id>/update/', CouponUpdateView.as_view(), name='coupon-update'),
    path('admin/coupons/<int:coupon_id>/none_active/', CouponDeleteView.as_view(), name='coupon-delete'),
    path('admin/statistics/', AdminStatisticsView.as_view(), name='admin-statistics'),

    path("admin/driver/pending/", AdminPendingWorkersView.as_view()),
    path("admin/driver/approve/", AdminApproveWorkerView.as_view()),
    path("admin/driver/reject/", AdminRejectWorkerView.as_view()),
]