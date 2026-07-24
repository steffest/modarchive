from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from homepage import legacy_models
User = get_user_model()

class Command(BaseCommand):
    help = "Migrate the xml keys table to new api keys"

    def handle(self, *args, **options):
        xml_keys = legacy_models.TmaXmlKeys.objects.using('legacy').all()

        for xml_key in xml_keys:
            # Skip if length of xmlkey is > 40 characters
            if len(xml_key.xmlkey) > 40:
                print(f"Skipping {xml_key.id} because it's too long")
                continue

            print(f"Migrating id {xml_key.id}")
            # Create a dummy user
            user = User.objects.create(
                username='xml_key_user_' + str(xml_key.id),
                password=xml_key.xmlkey,
                email=xml_key.owner,
                is_staff=False
            )

            # Create a token for the dummy user with the same key as the xml_key
            Token.objects.create(user=user, key=xml_key.xmlkey)
