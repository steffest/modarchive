from django.test import TestCase
from django.urls import reverse

from songs.factories import SongFactory, SongStatsFactory, SongRedirectFactory
from artists.factories import ArtistFactory
from interactions.factories import CommentFactory, FavoriteFactory, ArtistCommentFactory
from homepage.tests import factories

class ViewSongTests(TestCase):
    FILE_2_FILENAME = "file2.s3m"
    FILE_2_TITLE = "File 2"

    COMMENT_TEXT_1 = "This was definitely a song!"
    COMMENT_TEXT_2 = "I disagree, this was not a song."

    def test_context_contains_song_and_comments(self):
        song = SongFactory(filename=self.FILE_2_FILENAME, title=self.FILE_2_TITLE)
        SongStatsFactory(song=song)
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))
        CommentFactory(song=song, rating=10, text=self.COMMENT_TEXT_1)
        CommentFactory(song=song, rating=5, text=self.COMMENT_TEXT_2)

        self.assertTrue('song' in response.context)
        song = response.context['song']
        self.assertEqual(self.FILE_2_FILENAME, song.filename)
        self.assertEqual(self.FILE_2_TITLE, song.get_title())
        self.assertEqual(2, len(song.comment_set.all()))
        self.assertEqual(self.COMMENT_TEXT_1, song.comment_set.all()[1].text)
        self.assertEqual(self.COMMENT_TEXT_2, song.comment_set.all()[0].text)
        self.assertEqual(10, song.comment_set.all()[1].rating)
        self.assertEqual(5, song.comment_set.all()[0].rating)

    def test_unauthenticated_user_cannot_comment(self):
        # Arrange
        song = SongFactory(
            filename=self.FILE_2_FILENAME,
            title="File 2"
        )

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse('can_comment' in response.context)

    def test_user_can_comment_if_has_not_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertTrue(response.context['can_comment'])

    def test_user_cannot_comment_if_has_already_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory()
        CommentFactory(
            song=song,
            profile=user.profile,
            rating=10,
            text="This was definitely a song!"
        )
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['can_comment'])

    def test_user_can_comment_when_not_the_song_composer(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory()
        ArtistFactory(songs=(song,))
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertTrue(response.context['can_comment'])

    def test_user_cannot_comment_if_is_song_composer(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory()
        ArtistFactory(songs=(song,), profile=user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['can_comment'])

    def test_is_favorite_is_not_present_when_not_authenticated(self):
        # Arrange
        song = SongFactory()

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(hasattr(response.context, 'is_favorite'))

    def test_is_favorite_is_false_when_not_favorited(self):
        # Arrange
        song = SongFactory()
        user = factories.UserFactory()
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['is_favorite'])

    def test_is_favorite_is_true_when_favorited(self):
        # Arrange
        song = SongFactory()
        user = factories.UserFactory()
        self.client.force_login(user)
        FavoriteFactory(profile=user.profile, song=song)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertTrue(response.context['is_favorite'])

    def test_artist_can_comment_is_false_when_own_song_and_has_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory()
        ArtistFactory(songs=[song], user=user, profile=user.profile)
        ArtistCommentFactory(song=song, profile=user.profile, text="hi")
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['artist_can_comment'])

    def test_artist_can_comment_is_true_when_own_song_and_has_not_commented(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory()
        ArtistFactory(songs=[song], user=user, profile=user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertTrue(response.context['artist_can_comment'])

    def test_artist_can_comment_is_false_when_not_own_song(self):
        # Arrange
        user = factories.UserFactory()
        song = SongFactory()
        ArtistFactory(songs=[], user=user, profile=user.profile)
        self.client.force_login(user)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(response.context['artist_can_comment'])

    def test_artist_can_comment_is_not_present_when_not_authenticated(self):
        # Arrange
        song = SongFactory()

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': song.id}))

        # Assert
        self.assertFalse(hasattr(response.context, 'artist_can_comment'))

    def test_uses_song_redirect_when_available(self):
        # Arrange
        song = SongFactory()
        SongRedirectFactory(song=song, old_song_id=500)

        # Act
        response = self.client.get(reverse('view_song', kwargs = {'pk': 500}))

        # Assert
        self.assertRedirects(response, reverse('view_song', kwargs = {'pk': song.id}), status_code=301)
