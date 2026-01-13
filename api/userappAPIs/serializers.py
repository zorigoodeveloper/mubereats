from rest_framework import serializers
from ..database import execute_query
from django.contrib.auth.models import User

class CartItemSerializer(serializers.Serializer):
    service_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(default=1, min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class AddToCartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True, required=True)


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, required=False)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)

class UserSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()

class ProfileSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    location = serializers.CharField()

class CustomerSignUpSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(write_only=True, min_length=6, required=True)
    full_name = serializers.CharField(max_length=255, required=True)
    
    # Optional fields
    default_address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8, required=False, allow_null=True)

    def validate_email(self, value):
        """Имэйл давхардаж байгаа эсэх шалгах"""
        existing = execute_query(
            "SELECT 1 FROM users WHERE email = %s",
            (value,),
            fetch_one=True
        )
        if existing:
            raise serializers.ValidationError("Энэ имэйл аль хэдийн бүртгэлтэй байна.")
        return value

    def validate_phone_number(self, value):
        """Утасны дугаар давхардаж байгаа эсэх шалгах"""
        existing = execute_query(
            "SELECT 1 FROM users WHERE phone_number = %s",
            (value,),
            fetch_one=True
        )
        if existing:
            raise serializers.ValidationError("Энэ утасны дугаар аль хэдийн бүртгэлтэй байна.")
        return value


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

class OrderItemSerializer(serializers.Serializer):
    foodID = serializers.IntegerField()
    stock = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

class OrderCreateSerializer(serializers.Serializer):
    restaurant_id = serializers.IntegerField()
    delivery_address = serializers.CharField(max_length=500)
    items = OrderItemSerializer(many=True)