import operator
from functools import reduce

from django.dispatch import receiver

from django.contrib.postgres.search import SearchVector
from django.db.models.signals import post_save, pre_save

from artists.models import Artist
from songs.models import Song

@receiver(pre_save, sender=Song)
def track_song_changes(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Song.objects.only('title', 'instrument_text', 'comment_text').get(pk=instance.pk)
        instance._indexed_fields_changed = (
            old_instance.title != instance.title or
            old_instance.instrument_text != instance.instrument_text or
            old_instance.comment_text != instance.comment_text
        )
    else:
        instance._indexed_fields_changed = False

@receiver(post_save, sender=Song)
def index_song(sender, **kwargs):
    song = kwargs['instance']

    # Only index if title, comment text or instrument text have changed
    if kwargs['created'] or getattr(song, '_indexed_fields_changed', False):
        title_vector=reduce(operator.add, [SearchVector('title')])
        instrument_text_vector=reduce(operator.add, [SearchVector('instrument_text')])
        comment_text_vector=reduce(operator.add, [SearchVector('comment_text')])

        song.__class__.objects.filter(pk=song.pk).update(
            title_vector=title_vector,
            instrument_text_vector=instrument_text_vector,
            comment_text_vector=comment_text_vector
        )

@receiver(pre_save, sender=Artist)
def track_artist_changes(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Artist.objects.get(pk=instance.pk)
        instance._name_changed = old_instance.name != instance.name
    else:
        instance._name_changed = False

@receiver(post_save, sender=Artist)
def index_artist(sender, **kwargs):
    artist=kwargs['instance']

    # Only index on create or if name actually changed
    if kwargs['created'] or getattr(artist, '_name_changed', False):
        artist.__class__.objects.filter(pk=artist.pk).update(
            search_document=reduce(operator.add, [SearchVector('name')])
        )