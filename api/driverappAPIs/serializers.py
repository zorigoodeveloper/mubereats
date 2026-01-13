from rest_framework import serializers

class WorkerSerializer(serializers.Serializer):
    workerName = serializers.CharField(max_length=255)
    phone = serializers.IntegerField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    vehicleType = serializers.CharField()  # FK ID
    vehicleReg = serializers.CharField(max_length=20)


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)