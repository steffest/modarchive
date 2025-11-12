from django.views.generic import ListView
from django.shortcuts import redirect, get_object_or_404

from artists.models import Artist
from songs.models import Song
from homepage.views.common_views import PageNavigationListView

class ArtistDetailView(PageNavigationListView):
    model = Song
    template_name = "artist_overview.html"

    def get(self, request, *args, **kwargs):
        # Load only the artist (no song queries yet)
        self.artist = get_object_or_404(Artist, pk=self.kwargs["pk"])

        # If artist has a profile, redirect before any song query
        if hasattr(self.artist, "profile") and self.artist.profile is not None:
            return redirect("view_profile", self.artist.profile.id)

        # Otherwise continue with normal page rendering
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["artist"] = self.artist
        return context_data

    def get_queryset(self):
        # Only called if we didn’t redirect
        return self.artist.songs.all().order_by('-create_date')

class ArtistListView(ListView):
    model = Artist
    template_name='artist_list.html'
    queryset=Artist.objects.order_by('-id')[:50]