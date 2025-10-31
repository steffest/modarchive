import re

from django.shortcuts import redirect

from django.urls import reverse

from homepage.views.common_views import PageNavigationListView
from songs.models import Song

BROWSE_SONGS_TEMPLATE = 'browse_songs.html'

class BrowseSongsByLicenseView(PageNavigationListView):
    model = Song
    template_name = BROWSE_SONGS_TEMPLATE
    paginate_by = 40

    def dispatch(self, request, *args, **kwargs):
        query = kwargs['query']
        if query not in dict(Song.Licenses.choices).keys():
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.kwargs['query']
        context['licenses'] = Song.Licenses.choices
        context['options'] = [(code, name, reverse('browse_by_license', kwargs={'query': code})) for code, name in Song.Licenses.choices]
        context['label'] = 'license'
        return context

    def get_queryset(self):
        return Song.objects.filter(license=self.kwargs['query']).order_by('filename')

class BrowseSongsByFilenameView(PageNavigationListView):
    model = Song
    template_name = BROWSE_SONGS_TEMPLATE
    paginate_by = 40

    def dispatch(self, request, *args, **kwargs):
        query = kwargs['query']
        if not re.fullmatch(r'^\w+$', query):
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.kwargs['query']
        context['options'] = [(char, char, reverse('browse_by_filename', kwargs={'query': char})) for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"]
        context['label'] = 'filename'
        return context

    def get_queryset(self):
        return Song.objects.filter(filename__istartswith=self.kwargs['query']).order_by('filename')

class BrowseSongsByGenreView(PageNavigationListView):
    model = Song
    template_name = BROWSE_SONGS_TEMPLATE
    paginate_by = 40

    def dispatch(self, request, *args, **kwargs):
        query = kwargs['query']

        if query not in dict(Song.Genres.choices).keys():
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.kwargs['query']
        context['options'] = [(id, name, reverse('browse_by_genre', kwargs={'query': id})) for id, name in Song.Genres.choices]
        context['label'] = 'genre'

        return context

    def get_queryset(self):
        return Song.objects.filter(genre=self.kwargs['query']).order_by('filename')

class BrowseSongsByRatingView(PageNavigationListView):
    model = Song
    template_name = BROWSE_SONGS_TEMPLATE
    paginate_by = 40

    def dispatch(self, request, *args, **kwargs):
        query = kwargs['query']

        if not query or query < 1 or query > 9:
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.kwargs['query']
        context['options'] = [(score, score, reverse('browse_by_rating', kwargs={'query': score})) for score in [9, 8, 7, 6, 5, 4, 3, 2, 1]]
        context['label'] = 'rating'

        return context

    def get_queryset(self):
        if self.kwargs['query'] == 9:
            return Song.objects.filter(songstats__average_comment_score__gte=9).order_by('-songstats__average_comment_score', 'filename')
        else:
            return Song.objects.filter(songstats__average_comment_score__lt=self.kwargs['query']+1, songstats__average_comment_score__gte=self.kwargs['query']).order_by('-songstats__average_comment_score', 'filename')
