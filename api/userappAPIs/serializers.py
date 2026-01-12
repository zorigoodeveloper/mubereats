from rest_framework import serializers

class SignUpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(max_length=255)
    user_type = serializers.ChoiceField(choices=['customer', 'driver', 'restaurant'])
    
    # Optional fields for driver
    license_number = serializers.CharField(max_length=50, required=False)
    vehicle_type = serializers.CharField(max_length=50, required=False)
    vehicle_plate = serializers.CharField(max_length=20, required=False)
    
    # Optional fields for customer
    default_address = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8, required=False, allow_null=True)

class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)