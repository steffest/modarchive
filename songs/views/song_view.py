from django.views.generic import DetailView
from django.http import Http404
from django.shortcuts import redirect
from songs.models import Song, SongRedirect

class SongView(DetailView):
    template_name='song_bootstrap.html'
    model=Song

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            if SongRedirect.objects.filter(old_song_id=self.kwargs['pk']).exists():
                song_id = SongRedirect.objects.get(old_song_id=self.kwargs['pk']).song_id
                return redirect('view_song', song_id, permanent=True)
            else:
                raise

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context['is_own_song'] = context['song'].is_own_song(self.request.user.profile.id)
            context['can_comment'] = context['song'].can_user_leave_comment(self.request.user.profile.id)
            context['is_favorite'] = self.request.user.profile.favorite_set.filter(song_id=context['song'].id).count() > 0
            context['artist_can_comment'] = context['is_own_song'] and not context['song'].has_artist_commented(self.request.user.profile.id)

        context['stats'] = context['song'].get_stats()

        # Filter legacy reviews to only show non-pending ones
        context['legacy_reviews'] = context['song'].legacyreview_set.filter(pending=False)

        return context
