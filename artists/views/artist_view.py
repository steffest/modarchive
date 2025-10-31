from django.core.paginator import Paginator
from django.views.generic import DetailView, ListView

from artists.models import Artist
from songs.models import Song
from homepage.views.common_views import PageNavigationListView

class ArtistView(DetailView):
    model = Artist
    template_name = 'artist.html'

class ArtistDetailView(DetailView):
    model = Artist
    template_name = "artist_overview.html"

class ArtistSongsView(PageNavigationListView):
    model = Song
    template_name = "artist_songs.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['artist'] = self.artist
        return context_data

    def get_queryset(self):
        self.artist = Artist.objects.get(pk=self.kwargs['pk'])
        return self.artist.songs.all()

class ArtistFavoritesView(PageNavigationListView):
    model = Song
    template_name = "artist_favorites.html"
    items_per_page = 25
    context_object_name = 'favorites'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['artist'] = self.artist
        return context_data

    def get_queryset(self):
        self.artist = Artist.objects.get(pk=self.kwargs['pk'])
        return self.artist.profile.favorite_set.all()

class ArtistCommentsView(PageNavigationListView):
    model = Song
    template_name = "artist_comments.html"
    items_per_page = 15
    context_object_name = 'comments'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['artist'] = self.artist
        return context_data

    def get_queryset(self):
        self.artist = Artist.objects.get(pk=self.kwargs['pk'])
        return self.artist.profile.comment_set.all()

class ArtistListView(ListView):
    model = Artist
    template_name='artist_list.html'
    queryset=Artist.objects.order_by('-id')[:50]