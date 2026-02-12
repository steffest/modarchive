from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Creates initial auth groups with proper permissions'

    def handle(self, *args, **options):
        admin_models = [
            ('songs', 'song'),
            ('interactions', 'comment'),
            ('interactions', 'favorite'),
            ('interactions', 'artistcomment'),
            ('homepage', 'blacklisteddomain'),
            ('homepage', 'news'),
            ('homepage', 'profile'),
            ('homepage', 'message'),
            ('artists', 'artist'),
            ('auth', 'group'),
            ('auth', 'user'),
        ]

        standard_models = [
            ('interactions', 'comment'),
            ('interactions', 'favorite'),
            ('homepage', 'profile'),
            ('homepage', 'message'),
        ]

        artist_models = [
            ('interactions', 'comment'),
            ('interactions', 'favorite'),
            ('interactions', 'artistcomment'),
            ('homepage', 'profile'),
            ('homepage', 'message'),
            ('artists', 'artist'),
        ]

        self.create_screeners_group()
        self.create_group('Admins', admin_models)
        self.create_group('Standard', standard_models)
        self.create_group('Artists', artist_models)

    def create_screeners_group(self):
        group_name = 'Screeners'
        permission_codename = 'can_approve_songs'
        app_label = 'songs'

        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created group: {group_name}'))
        else:
            self.stdout.write(f'Group "{group_name}" already exists.')

        try:
            permission = Permission.objects.get(
                codename=permission_codename,
                content_type__app_label=app_label,
            )
            group.permissions.add(permission)
            self.stdout.write(self.style.SUCCESS(
                f'Added permission "{permission_codename}" to group "{group_name}"'
            ))
        except Permission.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    f'Permission "{permission_codename}" not found in app "{app_label}". '
                    f'Make sure migrations are applied.'
                )
            )

    def create_group(self, group_name: str, models_to_include: list[tuple[str, str]]):
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created group: {group_name}'))
        else:
            self.stdout.write(f'Group "{group_name}" already exists.')

        for app_label, model_name in models_to_include:
            try:
                content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                permissions = Permission.objects.filter(content_type=content_type)

                for perm in permissions:
                    group.permissions.add(perm)
                    self.stdout.write(self.style.SUCCESS(
                        f'Added permission "{perm.codename}" to group "{group_name}" (model: {model_name})'
                    ))
            except ContentType.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f'Model "{model_name}" not found in app "{app_label}". '
                        f'Make sure migrations are applied.'
                    )
                )

        if group_name == 'Standard':
            permission = Permission.objects.get(
                codename='can_upload_songs',
                content_type__app_label='uploads',
            )
            group.permissions.add(permission)
