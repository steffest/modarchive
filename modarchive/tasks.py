import logging
from django.db.models import Sum, Avg
from artists.models import Artist
from songs.models import SongStats

logger = logging.getLogger(__name__)

def daily_heartbeat():
    logger.info("Daily scheduled job ran successfully.")

def update_artist_stats():
    """
    Update stats for all artists:
    - total_songs: Count of all songs by the artist
    - total_downloads: Sum of downloads from all song stats
    - total_comments: Sum of comments from all song stats
    - average_song_rating: Average of review scores from all song stats
    """
    artists = Artist.objects.all()
    updated_count = 0

    for artist in artists:
        # Get all songs for this artist
        songs = artist.songs.all()

        # Calculate total songs
        total_songs = songs.count()

        # Get stats for all songs and calculate aggregates
        song_stats = SongStats.objects.filter(song__in=songs)

        # Calculate total downloads
        total_downloads_result = song_stats.aggregate(total=Sum('downloads'))
        total_downloads = total_downloads_result['total'] or 0

        # Calculate total comments
        total_comments_result = song_stats.aggregate(total=Sum('total_comments'))
        total_comments = total_comments_result['total'] or 0

        # Calculate average rating
        average_rating_result = song_stats.aggregate(avg=Avg('average_comment_score'))
        average_rating = average_rating_result['avg'] or 0

        # Update the artist
        artist.total_songs = total_songs
        artist.total_downloads = total_downloads
        artist.total_comments = total_comments
        artist.average_song_rating = average_rating
        artist.save()

        updated_count += 1

    logger.info(f"Updated stats for {updated_count} artists.")
