from django.core.management.base import BaseCommand
from django.db.models import Count, Avg

from songs.models import Song, SongStats


BATCH_SIZE = 1000

def _bulk_save(batch):
    SongStats.objects.bulk_update(
        batch,
        ['total_favorites', 'total_comments', 'average_comment_score'],
        batch_size=BATCH_SIZE
    )

class Command(BaseCommand):
    help = 'Recalculate the total number of favorites for each song and update SongStats.'

    def add_arguments(self, parser):
        parser.add_argument('--song_id', type=int, help='Limit the calculation to a single song ID.')

    def handle(self, *args, **options):
        song_id = options.get('song_id')

        songs = Song.objects.all()

        if song_id:
            songs = songs.filter(id=song_id)

        # Annotate everything in ONE query
        songs = songs.annotate(
            total_favorites=Count('favorite', distinct=True),
            total_comments=Count('comment', distinct=True),
            average_comment_score=Avg('comment__rating'),
        ).select_related('songstats')

        total = songs.count()
        print(f"Starting to recalculate stats for {total} songs.")

        batch = []
        counter = 0

        for song in songs.iterator(chunk_size=BATCH_SIZE):
            song_stats = song.songstats

            song_stats.total_favorites = song.total_favorites
            song_stats.total_comments = song.total_comments
            song_stats.average_comment_score = song.average_comment_score

            batch.append(song_stats)
            counter += 1

            if len(batch) >= BATCH_SIZE:
                _bulk_save(batch)
                print(f"Recalculated stats for {counter} songs.")
                batch = []

        # Save remaining
        if batch:
            _bulk_save(batch)

        self.stdout.write(self.style.SUCCESS('Successfully recalculated song stats.'))

