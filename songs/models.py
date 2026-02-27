from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.conf import settings

from homepage.models import Profile

class Song(models.Model):
    class Formats(models.TextChoices):
        _669 = '669', _('669: Composer 669 / UNIS 669')
        AHX = 'AHX', _('AHX: Abyss\' Highest eXperience, formerly THX')
        AMF = 'AMF', _('AMF: ASYLUM / DSMI')
        AMS = 'AMS', _('AMS: Extreme\'s Tracker / Velvet Studio')
        C67 = 'C67', _('C67: CDFM / Composer 670')
        DBM = 'DBM', _('DBM: Digi Booster Pro')
        DIGI = 'DIGI', _('DIGI: Digi Booster')
        DMF = 'DMF', _('DMF: X-Tracker')
        DSM = 'DSM', _('DSM: DSIK')
        DSYM = 'DSYM', _('DSYM: Digital Symphony')
        DTM = 'DTM', _('DTM: Digital Tracker / Digital Home Studio')
        FAR = 'FAR', _('FAR: Farandole Composer')
        FMT = 'FMT', _('FMT: FM Tracker')
        GDM = 'GDM', _('GDM: BWSB Sound System')
        HVL = 'HVL', _('HVL: HivelyTracker')
        IMF = 'IMF', _('IMF: Imago Orpheus')
        IT = 'IT', _('IT: Impulse Tracker')
        J2B = 'J2B', _('J2B: Galaxy Sound System')
        MED = 'MED', _('MED: Octamed')
        MDL = 'MDL', _('MDL: Digitrakker')
        MO3 = 'MO3', _('MO3: Compressed Module')
        MOD = 'MOD', _('MOD: Protracker, Generic MOD')
        MPTM = 'MPTM', _('MPTM: OpenMPT')
        MT2 = 'MT2', _('MT2: MadTracker 2')
        MTM = 'MTM', _('MTM: Multi Tracker')
        OKT = 'OKT', _('OKT: Oktalyzer')
        PLM = 'PLM', _('PLM: Disorder Tracker 2')
        PSM = 'PSM', _('PSM: Epic MegaGames MASI')
        PTM = 'PTM', _('PTM: PolyTracker')
        S3M = 'S3M', _('S3M: Scream Tracker 3')
        SFX = 'SFX', _('SFX: SoundFX / MultiMedia Sound')
        STM = 'STM', _('STM: Scream Tracker')
        STP = 'STP', _('STP: SoundTracker Pro II')
        STX = 'STX', _('STX: Scream Tracker Music Interface Kit')
        SymMOD = 'SymMOD', _('SymMOD: Symphonie / Symphonie Pro')
        ULT = 'ULT', _('ULT: UltraTracker')
        UMX = 'UMX', _('UMX: Unreal Music')
        XM = 'XM', _('XM: FastTracker 2')

    class Licenses(models.TextChoices):
        PUBLIC_DOMAIN = 'publicdomain', _('Public Domain')
        NON_COMMERCIAL = 'by-nc', _('Non-commercial')
        NON_COMMERCIAL_NO_DERIVATIVES = 'by-nc-nd', _('Non-commercial No Derivatives')
        NON_COMMERCIAL_SHARE_ALIKE = 'by-nc-sa', _('Non-commercial Share Alike')
        NO_DERIVATIVES = 'by-nd', _('No Derivatives')
        SHARE_ALIKE = 'by-sa', _('Share Alike')
        ATTRIBUTION = 'by', _('Attribution')
        CC0 = 'cc0', _('CC0')

    class Genres(models.TextChoices):
        ELECTRONIC_TECHNO = 'electronic-techno', _("Electronic - Techno")
        ELECTRONIC_DANCE = 'electronic-dance', _("Electronic - Dance")
        ELECTRONIC_AMBIENT = 'electronic-ambient', _("Electronic - Ambient")
        ELECTRONIC_TRANCE_GENERAL = 'trance-general', _("Trance - General")
        ELECTRONIC_OTHER = 'electronic-other', _("Electronic - Other")
        ELECTRONIC_GENERAL = 'electronic-general', _("Electronic - General")
        ELECTRONIC_DRUM_AND_BASS = 'electronic-drum-and-bass', _("Electronic - Drum & Bass")
        ELECTRONIC_HOUSE = 'electronic-house', _("Electronic - House")
        ELECTRONIC_RAVE = 'electronic-rave', _("Electronic - Rave")
        ELECTRONIC_TRANCE_DREAM = 'trance-dream', _("Trance - Dream")
        ELECTRONIC_BREAKBEAT = 'electronic-breakbeat', _("Electronic - Breakbeat")
        ELECTRONIC_INDUSTRIAL = 'electronic-industrial', _("Electronic - Industrial")
        ELECTRONIC_HARDCORE = 'electronic-hardcore', _("Electronic - Hardcore")
        ELECTRONIC_CHILLOUT = 'chillout', _("Chillout")
        ELECTRONIC_TRANCE_GOA = 'trance-goa', _("Trance - Goa")
        ELECTRONIC_JUNGLE = 'electronic-jungle', _("Electronic - Jungle")
        ELECTRONIC_TRANCE_ACID = 'trance-acid', _("Trance - Acid")
        ELECTRONIC_IDM = 'electronic-idm', _("Electronic - IDM")
        ELECTRONIC_PROGRESSIVE = 'electronic-progressive', _("Electronic - Progressive")
        ELECTRONIC_GABBER = 'electronic-gabber', _("Electronic - Gabber")
        ELECTRONIC_MINIMAL = 'electronic-minimal', _("Electronic - Minimal")
        ELECTRONIC_TRANCE_HARD = 'trance-hard', _("Trance - Hard")
        ELECTRONIC_TRANCE_PROGRESSIVE = 'trance-progressive', _("Trance - Progressive")
        ELECTRONIC_TRANCE_TRIBAL = 'trance-tribal', _("Trance - Tribal")
        DEMO_CHIPTUNE = 'chiptune', _("Chiptune")
        DEMO_STYLE = 'demostyle', _("Demostyle")
        DEMO_1HRCOMPO = 'one-hour-compo', _("One-Hour Compo")
        POP_GENERAL = 'pop-general', _("Pop - General")
        POP_SYNTH = 'pop-synth', _("Pop - Synth")
        POP_SOFT = 'pop-soft', _("Pop - Soft")
        POP_ROCK_GENERAL = 'rock-general', _("Rock - General")
        POP_ROCK_SOFT = 'rock-soft', _("Rock - Soft")
        POP_ROCK_HARD = 'rock-hard', _("Rock - Hard")
        POP_FUNK = 'funk', _("Funk")
        POP_DISCO = 'disco', _("Disco")
        POP_BALLAD = 'ballad', _("Ballad")
        POP_EASY_LISTENING = 'easy-listening', _("Easy Listening")
        OTHER_VIDEO_GAME = 'video-game', _("Video Game")
        OTHER_ORCH = 'orchestral', _("Orchestral")
        OTHER_CLASSICAL = 'classical', _("Classical")
        OTHER_PIANO = 'piano', _("Piano")
        OTHER_FANTASY = 'fantasy', _("Fantasy")
        OTHER_SOUNDTRACK = 'soundtrack', _("Soundtrack")
        OTHER_COMEDY = 'comedy', _("Comedy")
        OTHER_MEDIEVAL = 'medieval', _("Medieval")
        OTHER_SPIRITUAL = 'spiritual', _("Spiritual")
        OTHER_RELIGIOUS = 'religious', _("Religious")
        OTHER_EXPERIMENTAL = 'experimental', _("Experimental")
        OTHER_NEWAGE = 'new-age', _("New Age")
        OTHER_FOLK = 'folk', _("Folk")
        OTHER_COUNTRY = 'country', _("Country")
        OTHER_BLUEGRASS = 'bluegrass', _("Bluegrass")
        OTHER_WORLD = 'world', _("World")
        OTHER_WORLD_LATIN = 'world-latin', _("World - Latin")
        OTHER_FUSION = 'fusion', _("Fusion")
        OTHER_VOX_MONTAGE = 'vocal-montage', _("Vocal Montage")
        OTHER_OTHER = 'other', _("Other")
        ALTERNATIVE = 'alternative', _("Alternative")
        ALTERNATIVE_GOTHIC = 'gothic', _("Gothic")
        ALTERNATIVE_PUNK = 'punk', _("Punk")
        ALTERNATIVE_METAL = 'metal-general', _("Metal - General")
        ALTERNATIVE_METAL_EXTREME = 'metal-extreme', _("Metal - Extreme")
        ALTERNATIVE_GRUNGE = 'grunge', _("Grunge")
        JAZZ = 'jazz-general', _("Jazz - General")
        JAZZ_MODERN = 'jazz-modern', _("Jazz - Modern")
        JAZZ_ACID = 'jazz-acid', _("Jazz - Acid")
        JAZZ_BLUES = 'blues', _("Blues")
        JAZZ_SWING = 'swing', _("Swing")
        JAZZ_BIG_BAND = 'big-band', _("Big Band")
        HIP_HOP = 'hip-hop', _("Hip-Hop")
        REGGAE = 'reggae', _("Reggae")
        R_AND_B = 'r-n-b', _("R&B")
        SOUL = 'soul', _("Soul")
        SKA = 'ska', _("Ska")
        CHRISTMAS = 'christmas', _("Christmas")
        HALLOWEEN = 'halloween', _("Halloween")

    legacy_id=models.IntegerField(null=True, db_index=True, blank=True)
    filename=models.CharField(max_length=120, db_index=True)
    filename_unzipped = models.CharField(max_length=120, blank=True)
    title=models.CharField(max_length=120, db_index=True)
    title_from_file = models.CharField(max_length=120, blank=True)
    format=models.CharField(max_length=6, choices=Formats.choices, db_index=True)
    file_size=models.PositiveIntegerField()
    channels=models.PositiveSmallIntegerField()
    instrument_text=models.TextField(max_length=64000, blank=True, null=True)
    comment_text=models.TextField(max_length=64000, blank=True, null=True)
    hash=models.CharField(max_length=33)
    pattern_hash=models.CharField(max_length=16, null=True, blank=True)
    license=models.CharField(max_length=16, choices=Licenses.choices, null=True, blank=True)
    search_document=SearchVectorField(null=True, blank=True)
    genre=models.CharField(choices=Genres.choices, null=True, blank=True, db_index=True, max_length=32)
    is_featured=models.BooleanField(null=True, blank=True, db_index=True)
    featured_date=models.DateTimeField(null=True, blank=True)
    featured_by=models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='featured_by')
    folder=models.CharField(max_length=4)
    title_vector=SearchVectorField(null=True, blank=True)
    instrument_text_vector=SearchVectorField(null=True, blank=True)
    comment_text_vector=SearchVectorField(null=True, blank=True)
    uploaded_by=models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, db_index=True, related_name='uploaded_by')
    create_date=models.DateTimeField(default=timezone.now)
    update_date=models.DateTimeField(auto_now=True)

    def get_title(self) -> str:
        title = str(self.title).strip()
        return str(self.filename) if not title else title

    def is_own_song(self, profile_id):
        return self.artist_set.all().filter(profile_id=profile_id).exists()

    def has_commented(self, profile_id):
        return self.comment_set.all().filter(profile_id=profile_id).exists()

    def has_artist_commented(self, profile_id):
        return self.artistcomment_set.all().filter(profile_id=profile_id).exists()

    def can_user_leave_comment(self, profile_id):
        return not self.is_own_song(profile_id) and not self.has_commented(profile_id)

    def display_file_size(self):
        if self.file_size >= 1000000:
            return f'{"{:.2f}".format(self.file_size / 1000000)} MB'

        if self.file_size >= 10000:
            return f'{"{:.2f}".format(self.file_size / 1000)} KB'

        return f'{self.file_size} bytes'

    def get_stats(self):
        if hasattr(self, 'songstats'):
            return self.songstats

        return SongStats.objects.create(song=self)

    def get_archive_path(self):
        folder = '1_9' if self.folder == '0_9' else self.folder
        return f"{settings.MAIN_ARCHIVE_DIR}/{self.format.upper()}/{folder}/{self.filename}.zip"  # pylint: disable=no-member

    class Meta:
        indexes = [
            GinIndex(fields=['title_vector', 'instrument_text_vector', 'comment_text_vector'])
        ]

    def __str__(self) -> str:
        return f"{self.get_title()} [id: {self.pk}]"

class SongStats(models.Model):
    song = models.OneToOneField(
        Song,
        on_delete=models.CASCADE,
        primary_key=True
    )
    downloads=models.PositiveIntegerField(default=0)
    total_comments=models.PositiveSmallIntegerField(default=0)
    average_comment_score=models.DecimalField(default=0.0, decimal_places=1, max_digits=3, blank=True, null=True)
    total_reviews=models.PositiveSmallIntegerField(default=0)
    average_review_score=models.DecimalField(default=0.0, decimal_places=1, max_digits=3, blank=True, null=True)
    total_favorites=models.PositiveIntegerField(default=0)

class SongRedirect(models.Model):
    class Meta:
        verbose_name_plural = 'song redirects'

    legacy_old_song_id=models.IntegerField(null=True, db_index=True, blank=True)
    old_song_id=models.IntegerField(null=True, db_index=True, blank=True)
    song=models.ForeignKey(Song, on_delete=models.CASCADE)

    def clean(self):
        if self.legacy_old_song_id is None and self.old_song_id is None:
            raise ValidationError("Either legacy_old_song_id or old_song_id must be set")

        if self.legacy_old_song_id is not None and self.old_song_id is not None:
            raise ValidationError("Only one of legacy_old_song_id or old_song_id can be set")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
