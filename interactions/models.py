from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from songs.models import Song
from homepage.models import Profile

class Comment(models.Model):
    class Meta:
        ordering = ['-create_date']

    class Ratings(models.IntegerChoices):
        _1 = 1, _("1: Very poor")
        _2 = 2, _("2: Poor")
        _3 = 3, _("3: Listenable")
        _4 = 4, _("4: Good attempt")
        _5 = 5, _("5: Average")
        _6 = 6, _("6: Above average")
        _7 = 7, _("7: Enjoyable")
        _8 = 8, _("8: Very good")
        _9 = 9, _("9: Excellent")
        _10 = 10, _("10: Awesome")

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    text = models.TextField(max_length=5000)
    rating = models.PositiveSmallIntegerField(choices=Ratings.choices)
    create_date = models.DateTimeField(default=timezone.now)

class ArtistComment(models.Model):
    class Meta:
        unique_together = ('profile', 'song')
        verbose_name_plural = 'artist comments'
        db_table = 'songs_artist_comments'

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    text = models.TextField(max_length=5000)
    create_date = models.DateTimeField(default=timezone.now)
    update_date=models.DateTimeField(auto_now=True)

class Favorite(models.Model):
    class Meta:
        unique_together = ('profile', 'song')

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
