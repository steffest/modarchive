from django import forms
from django.contrib import admin
from artists.models import Artist, ArtistSong

class ArtistSongInlineForArtist(admin.TabularInline):
    model = ArtistSong
    extra = 1
    autocomplete_fields = ['song']

class ArtistAdminForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = '__all__'
        help_texts = {
            'profile': 'Select the user profile associated with this artist. Only a single user profile may be connected to an artist. If none is selected, this artist will be considered a non-user artist, who is not associated with any user account on the site.',
        }

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    form = ArtistAdminForm
    list_display = ('pk', 'name')
    fields = ('name', 'legacy_id', 'profile',)
    autocomplete_fields = ['profile']
    inlines = (ArtistSongInlineForArtist,)
    exclude = ('search_document', 'user', 'key')
    search_fields = ['name']
