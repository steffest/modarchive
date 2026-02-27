from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from interactions.models import Comment
from songs.models import Song

@receiver(post_save, sender=Comment)
def update_song_stats_after_save(_sender=None, instance=None, **kwargs):
    update_song_stats(instance.song)

@receiver(post_delete, sender=Comment)
def update_song_stats_after_delete(_sender=None, instance=None, **kwargs):
    update_song_stats(instance.song)

def update_song_stats(song):
    if not Song.objects.filter(pk=song.pk).exists():
        return

    stats = song.get_stats()
    total_comments = song.comment_set.all().count()
    stats.total_comments = total_comments
    stats.average_comment_score = get_average_rating(song, total_comments)
    stats.save()

def get_average_rating(song, total_comments):
    if total_comments == 0:
        return None

    return sum(comment.rating for comment in song.comment_set.all()) / total_comments
