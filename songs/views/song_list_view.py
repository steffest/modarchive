from django.views.generic import TemplateView
from songs.models import Song

class SongListView(TemplateView):
    template_name = 'song_list.html'
    random_songs_limit = 8

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['songs'] = Song.objects.order_by('?')[:self.random_songs_limit]
        return context

