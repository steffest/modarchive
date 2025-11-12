import re

from django.core.management.base import BaseCommand
from interactions.models import Comment, ArtistComment
from songs.models import Song
from homepage.models import Profile, Message

class Command(BaseCommand):
    help = 'Converts from bbcode to markdown for comments, profile blurbs and artist comments'

    def add_arguments(self, parser):
        parser.add_argument('--comments', action='store_true',
                            help='Convert bbcode to markdown for comments')
        parser.add_argument('--artist_comments', action='store_true',
                            help='Convert bbcode to markdown for artist comments')
        parser.add_argument('--profile_blurbs', action='store_true',
                            help='Convert bbcode to markdown for profile blurbs')
        parser.add_argument('--messages', action='store_true',
                            help='Convert bbcode to markdown for shoutwall messages')

    def handle(self, *args, **options):
        if options['comments']:
            self.convert_comments()
        elif options['artist_comments']:
            self.convert_artist_comments()
        elif options['messages']:
            self.convert_messages()
        else:
            self.convert_profile_blurbs()

    def convert_comments(self):
        comments = Comment.objects.all()
        counter = 0
        print(f"Converting bbcode for {len(comments)} comments.")

        for comment in comments:
            counter += 1

            text = comment.text
            text = self.convert_bold(text)
            text = self.convert_italic(text)
            # text = self.convert_modpage(text)

            if counter % 1000 == 0:
                print(f"Converted {counter} comments.")

            if comment.text != text:
                comment.text = text
                comment.save()

    def convert_artist_comments(self):
        artist_comments = ArtistComment.objects.all()
        counter = 0
        print(f"Converting bbcode for {len(artist_comments)} artist comments.")

        for comment in artist_comments:
            counter += 1

            text = comment.text
            text = self.convert_bold(text)
            text = self.convert_italic(text)
            text = self.convert_url(text)
            # text = self.convert_modpage(text)

            if counter % 1000 == 0:
                print(f"Converted {counter} comments.")

            if comment.text != text:
                comment.text = text
                comment.save()

    def convert_messages(self):
        messages = Message.objects.all()
        counter = 0
        print(f"Converting bbcode for {len(messages)} messages.")

        for message in messages:
            counter += 1

            text = message.text
            text = self.convert_bold(text)
            text = self.convert_italic(text)

            if counter % 1000 == 0:
                print(f"Converted {counter} messages.")

            if message.text != text:
                message.text = text
                message.save()

    def convert_profile_blurbs(self):
        profiles = Profile.objects.all()
        counter = 0
        print(f"Converting bbcode for {len(profiles)} profiles.")

        for profile in profiles:
            counter += 1

            text = profile.blurb

            if text is None:
                continue

            text = self.convert_bold(text)
            text = self.convert_italic(text)
            text = self.convert_url(text)
            # text = self.convert_modpage(text)
            # text = self.convert_modlinks(text)
            text = self.convert_head(text)
            text = self.convert_hr(text)

            if counter % 1000 == 0:
                print(f"Converted {counter} profiles.")

            if profile.blurb != text:
                profile.blurb = text
                profile.save()

    def convert_bold(self, text):
        return re.sub(r'\[b\](.*?)\[/b\]', r'**\1**', text, flags=re.IGNORECASE)

    def convert_italic(self, text):
        return re.sub(r'\[i\](.*?)\[/i\]', r'*\1*', text, flags=re.IGNORECASE)

    def convert_head(self, text):
        return re.sub(r'\[head\](.*?)\[/head\]',r'### \1', text, flags=re.IGNORECASE)

    def convert_hr(self, text):
        return re.sub(r'\[hr\]', r'***', text, flags=re.IGNORECASE)

    def convert_url(self, text):
        return re.sub(r'\[url=(.*?)\](.*?)\[/url\]', r'[\2](\1)', text, flags=re.IGNORECASE)

    # def convert_modpage(self, text):
    #     return re.sub(r'\[modpage\](\d+)\[/modpage\]', self.replace_modpage, text, flags=re.IGNORECASE)

    # def convert_modlinks(self, text):
    #     return re.sub(r'\[modlinks\](\d+)\[/modlinks\]', self.replace_modlinks, text, flags=re.IGNORECASE)

    # def replace_modpage(self, match):
    #     legacy_id = int(match.group(1))
    #     try:
    #         # Find the corresponding song with the legacy ID
    #         song = Song.objects.get(legacy_id=legacy_id)
    #         # Replace the [modpage] tag with the new song ID
    #         return f'[modpage]{song.id}[/modpage]'
    #     except Song.DoesNotExist:
    #         return match.group(0)

    # def replace_modlinks(self, match):
    #     legacy_id = int(match.group(1))
    #     try:
    #         # Find the corresponding song with the legacy ID
    #         song = Song.objects.get(legacy_id=legacy_id)
    #         # Replace the [modlinks] tag with the new song ID
    #         return f'[modlinks]{song.id}[/modlinks]'
    #     except Song.DoesNotExist:
    #         return match.group(0)
