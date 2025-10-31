from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.contrib.auth import get_user_model
from artists.models import Artist
from .disable_signals import DisableSignals
import sys

class Command(BaseCommand):
    help = "Set up local development data (users + fixtures)"

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != 'modarchive.settings.dev':
            print("This command can only be run with the dev settings module.")
            sys.exit(1)
        
        # Begin by creating auth groups
        try:
            call_command("loaddata", "homepage/fixtures/groups.json")
            self.stdout.write(self.style.SUCCESS(f"Loaded groups fixture"))
        except Exception as e:
            self.stdout.write(self.style.SUCCESS(f"Failed to load groups fixture"))
        
        # Disable signals to create users
        with DisableSignals():
            self.create_user('test-user', [1])
            self.create_user('superuser', [1, 2, 3, 4], True, True)
            self.create_user('test-artist', [1, 2])

        # Load remaining fixtures
        fixtures = [
            "homepage/fixtures/profiles.json",
            "songs/fixtures/songs.json",
            "artists/fixtures/artists.json",
        ]

        for fixture in fixtures:
            try:
                call_command("loaddata", fixture, verbosity=0)
                self.stdout.write(self.style.SUCCESS(f"Loaded fixture: {fixture}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to load {fixture}: {e}"))

        self.stdout.write(self.style.SUCCESS("Local data setup complete."))

    def create_user(self, username: str, groups: list[int], is_staff: bool = False, is_superuser: bool = False):
        User = get_user_model()
        user, created = User.objects.update_or_create(
            username=username,
            defaults={
                "email": f"{username}@example.com",
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "is_active": True,
            },
        )

        if created:
            user.set_password("tmatest")
            user.save()
            self.stdout.write(self.style.NOTICE(f"Created user '{username}' with password 'tmatest'"))
            
            for group_id in groups:
                try:
                    group = Group.objects.get(pk=group_id)
                    user.groups.add(group)
                    self.stdout.write(self.style.SUCCESS(f"Added '{username}' to group '{group.name}'"))
                except Group.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Group with pk={group_id} not found — skipping group assignment"))
            return user
        else:
            self.stdout.write(self.style.WARNING(f"User '{username}' already exists"))
