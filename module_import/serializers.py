from rest_framework import serializers

class ModuleItemSerializer(serializers.Serializer):
    modules = serializers.ListField(
        child=serializers.CharField(max_length=100)
    )