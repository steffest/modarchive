import random
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from homepage.models import Profile
from songs.models import Song

User = get_user_model()

class Artist(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        primary_key=False,
        null=True,
        blank=True
    )
    profile = models.OneToOneField(
        Profile,
        on_delete=models.SET_NULL,
        primary_key=False,
        null=True,
        blank=True
    )
    legacy_id=models.IntegerField(null=True, blank=True, help_text="User ID from the legacy Mod Archive site", db_index=True)
    key=models.CharField(max_length=32, db_index=True, blank=True)
    name=models.CharField(max_length=64)
    random_token=models.PositiveIntegerField(null=True, blank=True, help_text="Used for differentiating artists with the same name")
    songs=models.ManyToManyField(Song, through='ArtistSong', blank=True)
    total_songs=models.PositiveIntegerField(null=True, blank=True, default=0)
    total_downloads=models.PositiveIntegerField(null=True, blank=True, default=0)
    total_comments=models.PositiveIntegerField(null=True, blank=True, default=0)
    average_song_rating=models.FloatField(null=True, blank=True, default=0)
    search_document=SearchVectorField(null=True)
    create_date=models.DateTimeField(default=timezone.now)
    update_date=models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_document'])
        ]
        unique_together = [
            ['name', 'random_token']
        ]

    def index_components(self):
        return {
            'A': self.name
        }

    def __str__(self):
        return str(self.name)

class ArtistSong(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('artist', 'song')

@receiver(pre_save, sender=Artist)
def set_random_number(sender, instance, **kwargs):
    # Generate a random 4-digit number only if it's a new artist or if there is a conflict
    if instance._state.adding or Artist.objects.filter(name=instance.name, random_token=instance.random_token).exclude(pk=instance.pk).exists():
        instance.random_token = random.randint(1000, 9999)
