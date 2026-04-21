from django.urls import path

from songs.views.song_view import SongView
from songs.views.song_list_view import SongListView
from songs.views.download_song_view import DownloadSongView
from songs.views.player_view import PlayerView
from songs.views.song_details_view import SongDetailsView
from songs.views.random_song_view import RandomSongView
from songs.views.browse_songs_views import (
    BrowseSongsByLicenseView,
    BrowseSongsByFilenameView,
    BrowseSongsByGenreView,
    BrowseSongsByRatingView
)

urlpatterns = [
    path('', SongListView.as_view(), name='songs'),
    path('<int:pk>/', SongView.as_view(), {}, 'view_song'),
    path('<int:pk>/download', DownloadSongView.as_view(), name='download_song'),
    path('<int:pk>/song_details', SongDetailsView.as_view(), {}, 'song_details'),
    path('random/', RandomSongView.as_view(), {}, 'random_song'),
    path('player/', PlayerView.as_view(), {}, 'player'),
    path('browse/license/<str:query>/', BrowseSongsByLicenseView.as_view(), name='browse_by_license'),
    path('browse/filename/<str:query>/', BrowseSongsByFilenameView.as_view(), name='browse_by_filename'),
    path('browse/genre/<str:query>/', BrowseSongsByGenreView.as_view(), name='browse_by_genre'),
    path('browse/rating/<int:query>/', BrowseSongsByRatingView.as_view(), name='browse_by_rating'),
]
