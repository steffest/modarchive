import markdown
from markdown.inlinepatterns import InlineProcessor
import xml.etree.ElementTree as eTree

from django.urls import reverse
from songs.models import Song, SongRedirect

class ModpageInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        song_id = m.group(1)
        el = eTree.Element("a")

        try:
            # Fetch the song record
            song = Song.objects.only("id", "title").get(pk=song_id)
            url = reverse("view_song", args=[song.id])
            el.set("href", url)
            el.text = song.title
        except Song.DoesNotExist:
            # Look for a redirect
            if SongRedirect.objects.filter(old_song_id=song_id).exists():
                redirect = SongRedirect.objects.get(old_song_id=song_id)
                song = redirect.song
                url = reverse("view_song", args=[song.id])
                el.set("href", url)
                el.text = song.title
            else:
                # Graceful fallback
                el.set("href", "#")
                el.text = f"[missing song {song_id}]"

        return el, m.start(0), m.end(0)

class ModpageExtension(markdown.Extension):
    def extendMarkdown(self, md):
        # Match [[modpage:1234]]
        pattern = r"\[\[modpage:(\d+)\]\]"
        md.inlinePatterns.register(ModpageInlineProcessor(pattern), "modpage", 175)
