from django.test import TestCase
from django.urls.base import reverse

from artists import factories
from songs import factories as song_factories
from homepage.tests import factories as homepage_factories

class ArtistViewTests(TestCase):
    def test_artist_list_view_contains_all_artists(self):
        # Arrange
        expected_length = 15
        for _ in range(expected_length):
            factories.ArtistFactory()

        # Act
        response = self.client.get(reverse('artists'))

        # Assert
        actual_length = len(response.context['object_list'])
        self.assertEqual(expected_length, actual_length, f"Expected {expected_length} objects in artists list but got {actual_length}")
        self.assertTemplateUsed(response, 'artist_list.html')
    
    def test_redirects_to_profile_when_profile_exists_for_artist(self):
        # Arrange
        user = homepage_factories.UserFactory()
        artist = factories.ArtistFactory(name='Arcturus', legacy_id=69117, user=user, profile=user.profile)

        # Act
        response = self.client.get(reverse('view_artist', kwargs = {'pk': artist.id}))

        # Assert
        self.assertRedirects(response, reverse('view_profile', kwargs = {'pk': user.profile.id}))
    
    def test_contains_songs(self):
        # Arrange
        songs = [song_factories.SongFactory() for _ in range(10)]
        artist = factories.ArtistFactory(name='Arcturus', songs=songs)

        response = self.client.get(reverse('view_artist', kwargs = {'pk': artist.id}))

        self.assertEqual(10, len(response.context['songs']))

    def test_contains_first_page_of_songs(self):
        # Arrange
        songs = [song_factories.SongFactory() for _ in range(30)]
        artist = factories.ArtistFactory(name='Arcturus', songs=songs)
        expected_first_page = list(artist.songs.order_by("-create_date")[:25])

        # Act
        response = self.client.get(reverse('view_artist', kwargs = {'pk': artist.id}))

        # Assert
        self.assertEqual(response.status_code, 200)
        page_songs = list(response.context["songs"])
        self.assertEqual(len(page_songs), 25)
        self.assertEqual(page_songs, expected_first_page)
        self.assertEqual(artist, response.context['artist'])

    def test_contains_second_page_of_songs(self):
        # Arrange
        songs = [song_factories.SongFactory() for _ in range(30)]
        artist = factories.ArtistFactory(name='Arcturus', songs=songs)
        expected_second_page = list(artist.songs.order_by("-create_date")[25:])

        # Act
        response = self.client.get(reverse('view_artist', kwargs = {'pk': artist.id}) + "?page=2")

        # Assert
        self.assertEqual(response.status_code, 200)
        page_songs = list(response.context["songs"])
        self.assertEqual(len(page_songs), 5)
        self.assertEqual(page_songs, expected_second_page)
        self.assertEqual(artist, response.context['artist'])

class ArtistModelTests(TestCase):
    def test_creates_random_token_on_save(self):
        # Arrange
        artist = factories.ArtistFactory(name='Arcturus')

        # Act
        artist.save()

        # Assert
        self.assertIsNotNone(artist.random_token)

    def test_two_artists_with_same_name_have_different_random_tokens(self):
        # Arrange
        artist1 = factories.ArtistFactory(name='Arcturus')
        artist2 = factories.ArtistFactory(name='Arcturus')

        # Act
        artist1.save()
        artist2.save()

        # Assert
        self.assertNotEqual(artist1.random_token, artist2.random_token)
