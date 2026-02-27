from django.test import TestCase

from songs.factories import SongFactory, SongStatsFactory
from interactions.factories import CommentFactory

class CommentModelTests(TestCase):
    def test_song_stats_updated_correctly_after_removing_comment(self):
        song = SongFactory()
        SongStatsFactory(song=song)
        comment_1 = CommentFactory(song=song, rating=10)
        CommentFactory(song=song, rating=5)

        self.assertEqual(2, song.songstats.total_comments)
        self.assertEqual(7.5, song.songstats.average_comment_score)

        comment_1.delete()

        self.assertEqual(1, song.songstats.total_comments)
        self.assertEqual(5.0, song.songstats.average_comment_score)

    def test_song_stats_updated_correctly_after_removing_final_comment(self):
        song = SongFactory()
        SongStatsFactory(song=song)
        comment_1 = CommentFactory(song=song, rating=10)

        comment_1.delete()

        self.assertEqual(0, song.songstats.total_comments)
        self.assertEqual(None, song.songstats.average_comment_score)
