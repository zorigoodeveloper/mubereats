from django.urls import path
from .views import (
    CreateOrderView,
    CustomerSignUpView,
    SignInView,
    ProfileView,
    UserSearchAPIView,
    ProfileUpdateView,
    OrderListView,
    AddToCartView,
    CartView,
    CartItemUpdateView,
    CartItemDeleteView,
)
from .eViews import RestaurantOnlySearchAPIView, FoodOnlySearchAPIView
<<<<<<< HEAD
from .social_auth import SocialLoginView

=======
from .reviews import RestaurantReviewView, DriverReviewView, FoodReviewView
>>>>>>> 92fad0920202ce0f346fc81737036d17fd001e12

urlpatterns = [
    path('auth/signup/customer/', CustomerSignUpView.as_view(), name='signup'),
    path('auth/signin/customer/', SignInView.as_view(), name='signin'),

    path("user/search/", UserSearchAPIView.as_view(), name="user-search"),

    path('auth/profile/customer/', ProfileView.as_view(), name='profile'),
    path('auth/profile/update/customer/', ProfileUpdateView.as_view(), name='profile-update'),

    path('orders/create/', CreateOrderView.as_view()),
    path('order/list/', OrderListView.as_view(), name='order-list'),

    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/item/<int:cart_item_id>/', CartItemUpdateView.as_view(), name='cart-item-update'),
    path('cart/item/<int:cart_item_id>/delete/', CartItemDeleteView.as_view(), name='cart-item-delete'),

    # SEARCH
    path("restaurants/search/", RestaurantOnlySearchAPIView.as_view(), name="search-restaurants"),
    path("foods/search/", FoodOnlySearchAPIView.as_view(), name="search-foods"),

<<<<<<< HEAD
    path("auth/social/login/", SocialLoginView.as_view(), name="social-login"),

=======
    # REVIEWS
    path('reviews/restaurant/', RestaurantReviewView.as_view(), name='review-restaurant'),
    path('reviews/driver/', DriverReviewView.as_view(), name='review-driver'),
    path('reviews/food/', FoodReviewView.as_view(), name='review-food'),
>>>>>>> 92fad0920202ce0f346fc81737036d17fd001e12
]
