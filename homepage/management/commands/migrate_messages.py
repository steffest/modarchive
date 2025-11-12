from django.core.management import BaseCommand
from homepage import legacy_models
from homepage.models import Message, Profile

class Command(BaseCommand):
    help = 'Migrate the legacy messages table'

    def handle(self, *args, **options):
        messages_set = legacy_models.TmaProfileComments.objects.using('legacy').all().order_by('id')

        total = len(messages_set)

        print(f"Starting migration of {total} messages from tma_profile_comments table")
        successful=0
        message_id_map = {}

        for message in messages_set:
            try:
                text = message.text

                profile = Profile.objects.get(id=message.profile_userid)
                sender = Profile.objects.get(id=message.poster_userid)

                if message.reply_to_userid:
                    reply_recipient = Profile.objects.get(id=message.reply_to_userid)
                else:
                    reply_recipient = None

                if message.reply_to:
                    reply_to_message = message_id_map.get(message.reply_to)
                    if not reply_to_message:
                        continue
                    thread_starter_message = reply_to_message.thread_starter if reply_to_message and reply_to_message.thread_starter else reply_to_message
                else:
                    reply_to_message = None
                    thread_starter_message = None

                new_message = Message.objects.create(
                    profile=profile,
                    sender=sender,
                    text=text,
                    reply_recipient=reply_recipient,
                    reply_to=reply_to_message,
                    thread_starter=thread_starter_message,
                    create_date=message.date,
                )

                message_id_map[message.id] = new_message

                if message.reply_to and message.reply_to not in message_id_map:
                    print(f"Warning! {message.id} is a reply to {message.reply_to} but it is not in the map.")

                successful += 1
            except Profile.DoesNotExist:
                pass
                print(f"Could not find a profile for {message.profile_userid}")

        print(f"total successful messages: {successful} out of {total}")
