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
    image = serializers.CharField(required=False, allow_blank=True)
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


class FoodCategorySerializer(serializers.Serializer):
    catID = serializers.IntegerField(required=False)
    catName = serializers.CharField(max_length=100)


class FoodSerializer(serializers.Serializer):
    foodID = serializers.IntegerField(required=False)
    foodName = serializers.CharField(max_length=150)
    resID = serializers.IntegerField()
    catID = serializers.IntegerField()
    price = serializers.IntegerField()
    description = serializers.CharField(required=False, allow_blank=True)
    image = serializers.CharField(required=False, allow_blank=True)


class DrinkSerializer(serializers.Serializer):
    drink_id = serializers.IntegerField(required=False)
    drink_name = serializers.CharField(max_length=150)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)


class PackageSerializer(serializers.Serializer):
    package_id = serializers.IntegerField(required=False)
    restaurant_id = serializers.IntegerField()
    package_name = serializers.CharField(max_length=150)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class PackageFoodSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    package_id = serializers.IntegerField()
    food_id = serializers.IntegerField()
    quantity = serializers.IntegerField()


class PackageDrinkSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    package_id = serializers.IntegerField()
    drink_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
