from rest_framework import serializers

class SignUpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(max_length=255)
    user_type = serializers.ChoiceField(choices=['driver'])

    # Optional fields for driver
    license_number = serializers.CharField(max_length=50, required=False)
    vehicle_type = serializers.CharField(max_length=50, required=False)
    vehicle_plate = serializers.CharField(max_length=20, required=False)

class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)