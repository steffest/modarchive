from django.core.management.base import BaseCommand
from django.db import transaction

from homepage import legacy_models
from songs.models import Song, SongStats
from .disable_signals import DisableSignals

class Command(BaseCommand):
    help = "Migrate the legacy files table"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-compute lookup dictionaries for better performance
        self._genre_mapping = {
            0: None,
            1: Song.Genres.ELECTRONIC_GENERAL,
            2: Song.Genres.ELECTRONIC_AMBIENT,
            3: Song.Genres.ELECTRONIC_DANCE,
            58: Song.Genres.POP_DISCO,
            6: Song.Genres.ELECTRONIC_DRUM_AND_BASS,
            7: Song.Genres.ELECTRONIC_TECHNO,
            8: Song.Genres.OTHER_VIDEO_GAME,
            9: Song.Genres.ELECTRONIC_BREAKBEAT,
            10: Song.Genres.ELECTRONIC_HOUSE,
            11: Song.Genres.ELECTRONIC_PROGRESSIVE,
            12: Song.Genres.POP_GENERAL,
            13: Song.Genres.POP_ROCK_GENERAL,
            14: Song.Genres.POP_ROCK_HARD,
            15: Song.Genres.POP_ROCK_SOFT,
            18: Song.Genres.OTHER_COUNTRY,
            19: Song.Genres.JAZZ_BLUES,
            20: Song.Genres.OTHER_CLASSICAL,
            21: Song.Genres.OTHER_FOLK,
            22: Song.Genres.HIP_HOP,
            23: Song.Genres.OTHER_WORLD_LATIN,
            24: Song.Genres.SKA,
            25: Song.Genres.SOUL,
            26: Song.Genres.R_AND_B,
            27: Song.Genres.REGGAE,
            28: Song.Genres.OTHER_MEDIEVAL,
            29: Song.Genres.JAZZ,
            30: Song.Genres.JAZZ_ACID,
            31: Song.Genres.JAZZ_MODERN,
            32: Song.Genres.POP_FUNK,
            33: Song.Genres.ALTERNATIVE,
            34: Song.Genres.ELECTRONIC_INDUSTRIAL,
            35: Song.Genres.ALTERNATIVE_PUNK,
            36: Song.Genres.ALTERNATIVE_METAL,
            37: Song.Genres.ALTERNATIVE_METAL_EXTREME,
            38: Song.Genres.ALTERNATIVE_GOTHIC,
            39: Song.Genres.ELECTRONIC_HARDCORE,
            40: Song.Genres.ELECTRONIC_GABBER,
            41: Song.Genres.OTHER_OTHER,
            42: Song.Genres.OTHER_WORLD,
            43: Song.Genres.OTHER_SOUNDTRACK,
            44: Song.Genres.OTHER_NEWAGE,
            45: Song.Genres.OTHER_COMEDY,
            46: Song.Genres.OTHER_EXPERIMENTAL,
            47: Song.Genres.OTHER_SPIRITUAL,
            48: Song.Genres.ALTERNATIVE,
            49: Song.Genres.OTHER_RELIGIOUS,
            50: Song.Genres.OTHER_ORCH,
            52: Song.Genres.OTHER_FANTASY,
            53: Song.Genres.DEMO_1HRCOMPO,
            54: Song.Genres.DEMO_CHIPTUNE,
            55: Song.Genres.DEMO_STYLE,
            56: Song.Genres.POP_BALLAD,
            59: Song.Genres.OTHER_PIANO,
            60: Song.Genres.ELECTRONIC_JUNGLE,
            61: Song.Genres.POP_SYNTH,
            62: Song.Genres.POP_SOFT,
            63: Song.Genres.ELECTRONIC_TRANCE_ACID,
            64: Song.Genres.ELECTRONIC_TRANCE_HARD,
            65: Song.Genres.ELECTRONIC_RAVE,
            66: Song.Genres.ELECTRONIC_TRANCE_GOA,
            67: Song.Genres.ELECTRONIC_TRANCE_DREAM,
            68: Song.Genres.POP_EASY_LISTENING,
            70: Song.Genres.ELECTRONIC_TRANCE_TRIBAL,
            71: Song.Genres.ELECTRONIC_TRANCE_GENERAL,
            72: Song.Genres.CHRISTMAS,
            74: Song.Genres.JAZZ_BIG_BAND,
            75: Song.Genres.JAZZ_SWING,
            76: Song.Genres.OTHER_VOX_MONTAGE,
            85: Song.Genres.ELECTRONIC_TRANCE_PROGRESSIVE,
            99: Song.Genres.ELECTRONIC_IDM,
            100: Song.Genres.ELECTRONIC_OTHER,
            101: Song.Genres.ELECTRONIC_MINIMAL,
            102: Song.Genres.OTHER_FUSION,
            103: Song.Genres.ALTERNATIVE_GRUNGE,
            105: Song.Genres.OTHER_BLUEGRASS,
            106: Song.Genres.ELECTRONIC_CHILLOUT,
            107: Song.Genres.POP_EASY_LISTENING,
        }
        
        self._format_mapping = {
            'it': Song.Formats.IT,
            's3m': Song.Formats.S3M,
            'mod': Song.Formats.MOD,
            'xm': Song.Formats.XM,
            '669': Song.Formats._669,
            'ahx': Song.Formats.AHX,
            'amf': Song.Formats.AMF,
            'ams': Song.Formats.AMS,
            'c67': Song.Formats.C67,
            'dbm': Song.Formats.DBM,
            'digi': Song.Formats.DIGI,
            'dmf': Song.Formats.DMF,
            'dsm': Song.Formats.DSM,
            'dsym': Song.Formats.DSYM,
            'dtm': Song.Formats.DTM,
            'far': Song.Formats.FAR,
            'fmt': Song.Formats.FMT,
            'gdm': Song.Formats.GDM,
            'hvl': Song.Formats.HVL,
            'imf': Song.Formats.IMF,
            'j2b': Song.Formats.J2B,
            'mdl': Song.Formats.MDL,
            'med': Song.Formats.MED,
            'mo3': Song.Formats.MO3,
            'mptm': Song.Formats.MPTM,
            'mt2': Song.Formats.MT2,
            'mtm': Song.Formats.MTM,
            'okt': Song.Formats.OKT,
            'plm': Song.Formats.PLM,
            'psm': Song.Formats.PSM,
            'ptm': Song.Formats.PTM,
            'sfx': Song.Formats.SFX,
            'stm': Song.Formats.STM,
            'stp': Song.Formats.STP,
            'stx': Song.Formats.STX,
            'symmod': Song.Formats.SymMOD,
            'ult': Song.Formats.ULT,
            'umx': Song.Formats.UMX,
        }
        
        self._license_mapping = {
            'publicdomain': Song.Licenses.PUBLIC_DOMAIN,
            'by-nc': Song.Licenses.NON_COMMERCIAL,
            'by-nc-nd': Song.Licenses.NON_COMMERCIAL_NO_DERIVATIVES,
            'by-nc-sa': Song.Licenses.NON_COMMERCIAL_SHARE_ALIKE,
            'by-nd': Song.Licenses.NO_DERIVATIVES,
            'by-sa': Song.Licenses.SHARE_ALIKE,
            'by': Song.Licenses.ATTRIBUTION,
            'cc0': Song.Licenses.CC0,
        }

    def handle(self, *args, **options):
        with DisableSignals():
            # Use iterator() to avoid loading all records into memory
            files_queryset = legacy_models.Files.objects.using('legacy').all().order_by('id')
            total = files_queryset.count()

            print(f"Starting migrations of {total} files. This process will create all song and song_stats objects.")

            batch_size = 1000
            songs_to_create = []
            stats_to_create = []
            counter = 0

            # Process in batches for better performance
            for file in files_queryset.iterator(chunk_size=batch_size):
                counter += 1

                song_data, stats_data = self.prepare_song_data(file)
                songs_to_create.append(song_data)
                stats_to_create.append(stats_data)

                # Bulk create when batch is full or at the end
                if len(songs_to_create) >= batch_size or counter == total:
                    with transaction.atomic():
                        # Bulk create songs
                        created_songs = Song.objects.bulk_create(songs_to_create)
                        
                        # Update stats objects with the created song instances
                        for i, stats in enumerate(stats_to_create):
                            stats.song = created_songs[i]
                        
                        # Bulk create stats
                        SongStats.objects.bulk_create(stats_to_create)

                    print(f"Generated {counter} out of {total} from the legacy files table.")
                    
                    # Clear batches
                    songs_to_create = []
                    stats_to_create = []

    def prepare_song_data(self, legacy_file):
        # Generate song data
        create_date = legacy_file.date if legacy_file.date else legacy_file.timestamp

        if not str(legacy_file.songtitle).strip():
            title = legacy_file.filename
        else:
            title = legacy_file.songtitle

        song = Song(
            id = legacy_file.id,
            legacy_id = legacy_file.id,
            filename = legacy_file.filename,
            filename_unzipped = legacy_file.filename_unzipped,
            title = title,
            title_from_file = legacy_file.songtitle,
            format = self.get_format(legacy_file.format),
            file_size = legacy_file.filesize,
            channels = legacy_file.channels,
            instrument_text = legacy_file.insttext,
            comment_text = legacy_file.comment,
            hash = legacy_file.hash,
            pattern_hash = legacy_file.patternhash,
            license = self.get_license(legacy_file.license),
            create_date = create_date,
            update_date = legacy_file.timestamp,
            genre = self.get_genre(legacy_file.genre_id),
            folder = legacy_file.download
        )

        # Generate song stats data (song will be set after bulk create)
        stats = SongStats(
            downloads = legacy_file.hits,
            total_comments = legacy_file.comment_total,
            average_comment_score = legacy_file.comment_score,
            total_reviews = legacy_file.review_total,
            average_review_score = legacy_file.review_score,
        )

        return song, stats

    def get_genre(self, genre_id):
        return self._genre_mapping.get(genre_id, None)

    def get_format(self, format):
        return self._format_mapping.get(format, None)

    def get_license(self, license):
        return self._license_mapping.get(license, '')
