from rest_framework import serializers

from rest_framework import serializers

class RestaurantCategorySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=100)

class RestaurantSigninSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class RestaurantSerializer(serializers.Serializer):
    resID = serializers.IntegerField(required=False)  # auto-increment
    resName = serializers.CharField(max_length=150)
    catID = serializers.IntegerField()
    phone = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    lng = serializers.FloatField()
    lat = serializers.FloatField()
    openTime = serializers.TimeField()
    closeTime = serializers.TimeField()
    description = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False)
    status = serializers.ChoiceField(choices=['active', 'inactive'], required=False, default='active')

    # ----------------------------
    # Field validation functions
    # ----------------------------
    def validate_lat(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_lng(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value


# class BranchSerializer(serializers.Serializer):
#     branchID = serializers.IntegerField(required=False)
#     branchName = serializers.CharField(max_length=150)
#     resID = serializers.IntegerField()  # foreign key to restaurant
#     location = serializers.CharField(required=False, allow_blank=True)  # чиний "address"-ийг location болгож зөвшөөрсөн
#     phone = serializers.CharField(required=False, allow_blank=True)


# ------------------- FOOD CATEGORY -------------------
class FoodCategorySerializer(serializers.Serializer):
    catID = serializers.IntegerField(required=False)
    catName = serializers.CharField(max_length=100)

# ------------------- FOOD -------------------
class FoodSerializer(serializers.Serializer):
    foodID = serializers.IntegerField(read_only=True)
    foodName = serializers.CharField(max_length=150)
    resID = serializers.IntegerField()
    catID = serializers.IntegerField()
    price = serializers.IntegerField()
    description = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False)
    portion = serializers.CharField(max_length=50, required=False)  # Порц

# ------------------- DRINK -------------------
class DrinkSerializer(serializers.Serializer):
    drink_id = serializers.IntegerField(required=False)
    drink_name = serializers.CharField(max_length=150)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)
    pic = serializers.CharField(max_length=255, required=False) 
    resID = serializers.IntegerField() 

# ------------------- PACKAGE -------------------
class PackageSerializer(serializers.Serializer):
    package_id = serializers.IntegerField(required=False)
    restaurant_id = serializers.IntegerField()
    package_name = serializers.CharField(max_length=150)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    portion = serializers.CharField(max_length=50, required=False)
    img = serializers.CharField(max_length=255, required=False)
    def validate_price(self, value):
        """Price нь сөрөг байхгүй эсэхийг шалгах"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Үнэ сөрөг байж болохгүй")
        return value

# ------------------- PACKAGE FOOD -------------------
class PackageFoodSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    package_id = serializers.IntegerField()
    food_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    def validate(self, data):
        """Нэмэлт валидаци"""
        # Quantity нь 0-ээс их байх ёстой
        if data.get('quantity', 0) <= 0:
            raise serializers.ValidationError({"quantity": "Тоо хэмжээ 0-ээс их байх ёстой"})
        
        return data

# ------------------- PACKAGE DRINK -------------------
class PackageDrinkSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    package_id = serializers.IntegerField()
    drink_id = serializers.IntegerField()
    quantity = serializers.IntegerField()



# Serializer for each food in an order
class OrderFoodSerializer(serializers.Serializer):
    foodID = serializers.IntegerField()
    foodName = serializers.CharField(max_length=200)
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

# Serializer for each order
class RestaurantOrderSerializer(serializers.Serializer):
    orderID = serializers.IntegerField()
    userID = serializers.IntegerField()
    date = serializers.CharField()  # you can use serializers.DateTimeField() if you parse the date
    location = serializers.CharField(max_length=300)
    status = serializers.CharField(max_length=50)
    foods = OrderFoodSerializer(many=True)  # nested list of foods    


class RevenueReportSerializer(serializers.Serializer):
    restaurant_name = serializers.CharField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_food_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class DailyRevenueReportSerializer(serializers.Serializer):
    restaurant_name = serializers.CharField()
    date = serializers.DateField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)    