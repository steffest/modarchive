from django.urls import path

from artists.views import artist_view

urlpatterns = [
    path('', artist_view.ArtistListView.as_view(), {}, 'artists'),
    path('<int:pk>/', artist_view.ArtistDetailView.as_view(), {}, 'view_artist'),
]