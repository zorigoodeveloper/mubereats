from django.urls import path
from .views import (
    RestaurantCreateView,
    RestaurantListView, 
    RestaurantUpdateView, 
    RestaurantDeleteView,
    FoodCreateView, 
    FoodListView,
    PackageCreateView, 
    PackageAddFoodView, 
    PackageAddDrinkView,
    RestaurantCategoryCreateView,
    RestaurantCategoryListView,
    RestaurantCategoryUpdateView,
    RestaurantCategoryDeleteView,
    RestaurantStatusUpdateView, 
    RestaurantStatusCheckView,
    RestaurantSigninView
)

urlpatterns = [
    # Restaurant
    path('signup/', RestaurantCreateView.as_view()),
    path('signin/', RestaurantSigninView.as_view()),  # POST
    path('list/', RestaurantListView.as_view()),
    path('update/<int:resID>/', RestaurantUpdateView.as_view()),
    path('delete/<int:resID>/', RestaurantDeleteView.as_view()),

    # Food
    path('food/create/', FoodCreateView.as_view()),
    path('food/', FoodListView.as_view()),  # ?resID=

    # Package
    path('package/create/', PackageCreateView.as_view()),
    path('package/add-food/', PackageAddFoodView.as_view()),
    path('package/add-drink/', PackageAddDrinkView.as_view()),

    # category
    path('restype/', RestaurantCategoryCreateView.as_view(), name='restype-create'),
    path('restype/list/', RestaurantCategoryListView.as_view(), name='restype-list'),
    path('restype/update/<int:id>/', RestaurantCategoryUpdateView.as_view(), name='restype-update'),
    path('restype/delete/<int:id>/', RestaurantCategoryDeleteView.as_view(), name='restype-delete'),

    # status check
    path('update-status/<int:resID>/', RestaurantStatusUpdateView.as_view()),  # PATCH
    path('check-status/<int:resID>/', RestaurantStatusCheckView.as_view()),   # GET
]
