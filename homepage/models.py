from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        primary_key=False,
        null=True
    )
    legacy_id=models.IntegerField(null=True, db_index=True)
    display_name = models.CharField(max_length=255)
    blurb = models.TextField(max_length=24000, null=True, blank=True)
    enable_notifications = models.BooleanField(default=False)
    enable_shoutwall_notifications = models.BooleanField(default=False)
    enable_shoutwall = models.BooleanField(default=True)
    website = models.URLField(blank=True, null=True, max_length=100)
    create_date=models.DateTimeField(default=timezone.now)
    update_date=models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.display_name)

    def has_comments(self):
        return self.comment_set.all().count() > 0

class BlacklistedDomain(models.Model):
    domain=models.CharField(max_length=255, unique=True)
    hits=models.IntegerField(default=0)
    added_by=models.ForeignKey(User, on_delete=models.RESTRICT)
    create_date=models.DateTimeField(default=timezone.now)
    update_date=models.DateTimeField(auto_now=True)

class News(models.Model):
    class Meta:
        verbose_name_plural = "news items"

    headline=models.CharField(max_length=500)
    content=models.TextField(max_length=5000)
    profile=models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    create_date=models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now=True)
