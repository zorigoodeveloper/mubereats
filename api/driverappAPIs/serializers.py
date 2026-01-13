from rest_framework import serializers


class WorkerSerializer(serializers.Serializer):
    workerName = serializers.CharField(max_length=255)
    phone = serializers.IntegerField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    vehicleType = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    vehicleReg = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class DeliveryActionSerializer(serializers.Serializer):
    orderID = serializers.IntegerField()
    status = serializers.ChoiceField(choices=["accept", "picked_up", "delivered"])
