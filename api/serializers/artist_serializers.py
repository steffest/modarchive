from rest_framework import serializers
from artists.models import Artist


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = [
            'id',
            'name',
            'total_songs',
            'total_comments',
            'total_downloads',
            'average_song_rating',
        ]
