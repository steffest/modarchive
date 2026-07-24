from rest_framework import serializers

class GenreSerializer(serializers.Serializer):
    id = serializers.CharField()
    text = serializers.CharField()
