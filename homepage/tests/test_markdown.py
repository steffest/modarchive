from django.test import TestCase
from django.template import Context, Template
from django.urls import reverse
from songs import factories as song_factories

def render(text, profile):
    template = Template(
        "{% load markdown_extras %}{{ text|render_markdown:profile }}"
    )
    return template.render(Context({
        "text": text,
        "profile": profile,
    }))

class MarkdownTests(TestCase):
    def test_modpage_renders_internal_link(self):
        song = song_factories.SongFactory(title="Test Song")

        output = render(
            "Check this [[modpage:%d]]" % song.id,
            profile="default",
        )

        url = reverse("view_song", args=[song.id])

        self.assertIn(f'href="{url}"', output)
        self.assertIn("Test Song", output)
    
    def test_modpage_handles_redirect(self):
        song = song_factories.SongFactory(title="Redirected Song")
        song_factories.SongRedirectFactory(song=song, old_song_id=500)

        output = render(
            "Redirected [[modpage:500]]",
            profile="default",
        )

        url = reverse("view_song", args=[song.id])

        self.assertIn(f'href="{url}"', output)
        self.assertIn("Redirected Song", output)
    
    def test_modpage_handles_missing_id_gracefully(self):
        output = render(
            "Broken [[modpage:999999]]",
            profile="default",
        )

        self.assertIn("missing song", output.lower())
    
    def test_external_links_removed(self):
        output = render(
            "Visit https://example.com",
            profile="default",
        )

        self.assertNotIn("<a", output)
        self.assertIn("https://example.com", output)

    def test_external_links_allowed_when_enabled(self):
        output = render(
            "Visit https://example.com",
            profile="artist_comments",
        )

        self.assertIn('<a href="https://example.com"', output)
    
    def test_basic_formatting(self):
        output = render(
            "**bold** *italic* ~~strike~~",
            profile="default",
        )

        self.assertIn("<strong>bold</strong>", output)
        self.assertIn("<em>italic</em>", output)
        self.assertIn("<del>strike</del>", output)
    
    def test_extended_markdown_rendered(self):
        output = render(
            "### This is a header \n***\nAnd this is not",
            profile="profile_blurbs",
        )

        self.assertIn("<h3>This is a header</h3>", output)
        self.assertIn("<hr>", output)

    def test_unsupported_markdown_not_rendered(self):
        output = render(
            "# This is a big header",
            profile="default",
        )

        self.assertNotIn("<h1", output)
        self.assertIn("This is a big header", output)
    
    def test_raw_html_sanitized(self):
        output = render(
            "Hello <script>alert('xss')</script>",
            profile="default",
        )

        self.assertNotIn("<script>", output)
        self.assertIn("Hello", output)
