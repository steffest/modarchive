from django import template
from django.utils.safestring import mark_safe
import markdown
import bleach
import re
from homepage.markdown_extensions import ModpageExtension

register = template.Library()

# Profiles defining allowed output
MARKDOWN_PROFILES = {
    "default": {
        "tags": ["strong", "em", "u", "s", "a", "p", "del", "br"],
        "attributes": {"a": ["href", "title", "rel"]},
        "allow_external_links": False,
    },
    "artist_comments": {
        "tags": ["strong", "em", "u", "s", "a", "p", "del", "br"],
        "attributes": {"a": ["href", "title", "rel"]},
        "allow_external_links": True,
    },
    "profile_blurbs": {
        "tags": ["strong", "em", "u", "s", "a", "p", "del", "hr", "h3", "br", "ul", "li", "ol"],
        "attributes": {"a": ["href", "title", "rel"]},
        "allow_external_links": True,
    }
}

EXTERNAL_LINK_RE = re.compile(
    r'<a[^>]+href="https?://[^"]+"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)

def strip_external_links(html):
    """
    Remove external <a> tags but keep their text.
    Internal links (e.g. /songs/123/) are preserved.
    """
    return EXTERNAL_LINK_RE.sub(r'\1', html)

def _render_markdown(value, tags, attributes, allow_external_links):
    if not value:
        return ""

    # Step 1: Convert Markdown → HTML, but only for desired elements
    html = markdown.markdown(
        value,
        extensions=[
            ModpageExtension(),
            "nl2br",  # Preserve newlines,
            "pymdownx.tilde" # Strikethrough
        ],
        output_format="xhtml",
    )

    # Step 2: Clean HTML output (only allow your tags)
    clean_html = bleach.clean(
        html,
        tags=tags,
        attributes=attributes,
        strip=True,
    )

    # Step 3: If links are allowed, auto-link plain URLs
    if allow_external_links:
        clean_html = bleach.linkify(clean_html)
    else:
        clean_html = strip_external_links(clean_html)

    return mark_safe(clean_html)

@register.filter
def render_markdown(value, profile_name="default"):
    profile = MARKDOWN_PROFILES.get(profile_name, "default")
    return _render_markdown(
        value=value,
        tags=profile["tags"],
        attributes=profile["attributes"],
        allow_external_links=profile["allow_external_links"],
    )
