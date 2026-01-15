from django.urls import path
from .views import (
    # FoodImageUploadView,
    FoodImageUpdateView,
    ImageUploadView,
    RestaurantCreateView,
    RestaurantImageView,
    RestaurantImagesView,
    RestaurantListView,
    RestaurantMultipleImageUploadView,
    RestaurantUpdateView, 
    RestaurantDeleteView,
    FoodCreateView, 
    FoodListView,
    PackageCreateView, 
    # PackageAddFoodView, 
    # PackageAddDrinkView,
    RestaurantCategoryCreateView,
    RestaurantCategoryListView,
    RestaurantCategoryUpdateView,
    RestaurantCategoryDeleteView,
    RestaurantStatusUpdateView, 
    RestaurantStatusCheckView,
    RestaurantSigninView,
    RestaurantDetailView,
    # FoodCategory
    FoodCategoryListView, FoodCategoryCreateView, FoodCategoryUpdateView, FoodCategoryDeleteView,
    # Food
    FoodListView, FoodCreateView, FoodUpdateView, FoodDeleteView,
    # Drink
    DrinkListView, DrinkCreateView, DrinkUpdateView, DrinkDeleteView,
    # Package
    PackageListView, PackageCreateView, PackageUpdateView, PackageDeleteView,
    # PackageFood
    PackageFoodListView, PackageFoodCreateView, PackageFoodUpdateView, PackageFoodDeleteView,
    # PackageDrink
    PackageDrinkListView, PackageDrinkCreateView, PackageDrinkUpdateView, PackageDrinkDeleteView,
    # Image Upload
)
from .tViews import RestaurantOrderListView
from .confirm_order import ConfirmOrderView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Restaurant
    path('signup/', RestaurantCreateView.as_view()),
    path('signin/', RestaurantSigninView.as_view()),  # POST
    path('profileres/<int:res_id>/', RestaurantDetailView.as_view()),
    path('list/', RestaurantListView.as_view()),
    path('update/<int:resID>/', RestaurantUpdateView.as_view()),
    path('delete/<int:resID>/', RestaurantDeleteView.as_view()),
    
    path('<int:resID>/images/', RestaurantImagesView.as_view(), name='restaurant-images'),

    path('res/<int:resID>/image/info/', RestaurantImagesView.as_view(), name='restaurant-image-info'),
    path('<int:resID>/image/multiple/', RestaurantMultipleImageUploadView.as_view(), name='restaurant-image-uploads'),
    

    path('update/food/<int:foodID>/image/', FoodImageUpdateView.as_view(), name='food-image-upload'),
    path('upload/image/', ImageUploadView.as_view(), name='generic-image-upload'),
    path('res/<int:resID>/image/info/', RestaurantImageView.as_view(), name='restaurant-image-info'),

    # ------------------- FOOD -------------------
    path('<int:res_id>/foods/', FoodListView.as_view()),
    path('food/add/', FoodCreateView.as_view()),
    # path('food/add-with-image/', FoodCreateWithImageView.as_view()),
    path('food/update/<int:foodID>/', FoodUpdateView.as_view()),
    path('food/delete/<int:foodID>/', FoodDeleteView.as_view()),


    path('food-category/', FoodCategoryListView.as_view()),
    path('food-category/add/', FoodCategoryCreateView.as_view()),   
    path('food-category/update/<int:catID>/', FoodCategoryUpdateView.as_view()),
    path('food-category/delete/<int:catID>/', FoodCategoryDeleteView.as_view()),
    
    # ------------------- DRINK -------------------
    path('<int:res_id>/drink/', DrinkListView.as_view()),
    path('drink/add/', DrinkCreateView.as_view()),
    path('drink/update/<int:drink_id>/', DrinkUpdateView.as_view()),
    path('drink/delete/<int:drink_id>/', DrinkDeleteView.as_view()),

    # ------------------- PACKAGE -------------------
    path('package/', PackageListView.as_view()),
    path('package/add/', PackageCreateView.as_view()),
    path('package/update/<int:package_id>/', PackageUpdateView.as_view()),
    path('package/delete/<int:package_id>/', PackageDeleteView.as_view()),

    # ------------------- PACKAGE FOOD -------------------
    path('package-food/', PackageFoodListView.as_view()),
    path('package-food/add/', PackageFoodCreateView.as_view()),
    path('package-food/update/<int:id>/', PackageFoodUpdateView.as_view()),
    path('package-food/delete/<int:id>/', PackageFoodDeleteView.as_view()),

    # ------------------- PACKAGE DRINK -------------------
    path('package-drink/', PackageDrinkListView.as_view()),
    path('package-drink/add/', PackageDrinkCreateView.as_view()),
    path('package-drink/update/<int:id>/', PackageDrinkUpdateView.as_view()),
    path('package-drink/delete/<int:id>/', PackageDrinkDeleteView.as_view()),

    # category
    path('restype/add/', RestaurantCategoryCreateView.as_view(), name='restype-create'),
    path('restype/list/', RestaurantCategoryListView.as_view(), name='restype-list'),
    path('restype/update/<int:id>/', RestaurantCategoryUpdateView.as_view(), name='restype-update'),
    path('restype/delete/<int:id>/', RestaurantCategoryDeleteView.as_view(), name='restype-delete'),

    # status check
    path('update-status/<int:resID>/', RestaurantStatusUpdateView.as_view()),  # PATCH
    path('check-status/<int:resID>/', RestaurantStatusCheckView.as_view()),   # GET


    #order check
    path('orders/', RestaurantOrderListView.as_view()),
    path("order/confirm/", ConfirmOrderView.as_view()),

    # path('upload/<int:resID>/image/', RestaurantImageUploadView.as_view(), name='restaurant-image-upload'),
    # path('upload/food/<int:foodID>/image/', FoodImageUploadView.as_view(), name='food-image-upload'),
    # path('upload/image/', ImageUploadView.as_view(), name='generic-image-upload'),
    # path('res/<int:resID>/image/info/', RestaurantImageView.as_view(), name='restaurant-image-info'),
]
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)