from django.urls import reverse
from django.views.generic.base import RedirectView

from songs.models import Song, SongRedirect

class LegacyUrlRedirectionView(RedirectView):
    redirection_map = {
        'login': {
            'log_in': 'login'
        },
        'assistance': {
            'create_account_page': 'register',
            'forgot_password_page': 'forgot_password'
        },
        'interactive': {
            'change_password_page': 'change_password'
        },
        'index': {
            'view_by_moduleid': 'view_song'
        },
        'default': {
            'default': 'home'
        }
    }

    def get_redirect_url(self, *args, **kwargs):
        php_reference = kwargs.get('php_file', 'default')
        param = self.request.GET.get('request', 'default').lower()

        redirect_target = self.redirection_map.get(php_reference).get(param, 'home')

        kwargs = {}
        if redirect_target == 'view_song':
            legacy_module_id = self.request.GET.get('query')

            try:
                song = Song.objects.get(id = legacy_module_id)
                if song:
                    kwargs['pk'] = song.id
            except Song.DoesNotExist:
                try:
                    song_redirect = SongRedirect.objects.get(old_song_id = legacy_module_id)
                    if song_redirect:
                        kwargs['pk'] = song_redirect.song_id
                except SongRedirect.DoesNotExist:
                    redirect_target = 'home'

        return reverse(redirect_target, kwargs=kwargs)
