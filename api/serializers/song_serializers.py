from rest_framework import serializers
from songs.models import Song, SongStats
from artists.models import Artist

class SongStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SongStats
        fields = [
            'downloads',
            'total_comments',
            'average_comment_score',
            'total_favorites'
        ]

class LimitedArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = [
            'id',
            'name'
        ]

class SongDetailSerializer(serializers.ModelSerializer):
    stats = SongStatsSerializer(source='get_stats', read_only=True)
    artists = LimitedArtistSerializer(many=True, read_only=True, source='artist_set')
    
    class Meta:
        model = Song
        fields = [
            'id',
            'title',
            'title_from_file',
            'filename',
            'file_size',
            'channels',
            'format',
            'instrument_text',
            'comment_text',
            'license',
            'genre',
            'is_featured',
            'featured_date',
            'stats',
            'artists'
        ]

class SongListSerializer(serializers.ModelSerializer):
    artists = LimitedArtistSerializer(many=True, read_only=True, source='artist_set')
    
    class Meta:
        model = Song
        fields = [
            'id',
            'title',
            'title_from_file',
            'filename',
            'file_size',
            'channels',
            'format',
            'license',
            'genre',
            'is_featured',
            'artists'
        ]