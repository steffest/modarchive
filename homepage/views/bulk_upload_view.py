from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
import json

from homepage.forms import CsvUploadForm
from homepage.models import Profile
from songs.models import Song, SongStats
from artists.models import Artist

@method_decorator(login_required, name = 'dispatch')
@method_decorator(user_passes_test(lambda u: u.is_superuser, redirect_field_name=None), name = 'dispatch')
class BulkUploadView(View):
    def add_hashing_algorithm_to_password(self, password):
        if password.startswith("$2y"):
            return "bcrypt$" + password
        
        if password:
            return "hmac$" + password

        return password

    def generate_user(self, item):
        # Generate user
        username = item['username']
        password = self.add_hashing_algorithm_to_password(item['profile_password'])
        email = item['profile_email']
        is_staff = True if item['cred_admin'] else False
        date_joined = item['date']

        user = User.objects.create(username = username, password = password, email = email, date_joined = date_joined, is_staff = is_staff)

        # Generate profile
        profile = Profile.objects.create(
            user = user,
            display_name = item['profile_fullname'],
            blurb = item['profile_blurb'],
            create_date = date_joined,
            update_date = item['lastlogin'],
            legacy_id = item['userid']
        )

        # Generate artist
        if item['cred_artist']:
            artist = Artist.objects.create(
                user = user,
                profile = profile,
                legacy_id = item['userid'],
                name = item['profile_fullname'],
                create_date = date_joined,
                update_date = item['lastlogin']
            )

        return {'artist': artist, 'user': user, 'profile': profile}

    def get_format(self, format):
        match format:
            case 'it':
                return Song.Formats.IT
            case 's3m':
                return Song.Formats.S3M
            case 'mod':
                return Song.Formats.MOD
            case 'xm':
                return Song.Formats.XM
        return None

    def get_license(self, license):
        match license:
            case 'publicdomain':
                return Song.Licenses.PUBLIC_DOMAIN
            case 'by-nc':
                return Song.Licenses.NON_COMMERCIAL
            case 'by-nc-nd':
                return Song.Licenses.NON_COMMERCIAL_NO_DERIVATIVES
            case 'by-nc-sa':
                return Song.Licenses.NON_COMMERCIAL_SHARE_ALIKE
            case 'by-nd':
                return Song.Licenses.NO_DERIVATIVES    
            case 'by-sa':
                return Song.Licenses.SHARE_ALIKE
            case 'by':
                return Song.Licenses.ATTRIBUTION
            case 'cc0':
                return Song.Licenses.CC0
        return ''

    def generate_songs(self, file):
        # Generate song
        
        format = self.get_format(file['format'])
        license = self.get_license(file['license'])

        song = Song.objects.create(
            legacy_id = file['id'], 
            filename = file['filename'], 
            title = file['songtitle'], 
            format = format,
            file_size = file['filesize'],
            channels = file['channels'],
            instrument_text = file['insttext'],
            comment_text = file['comment'],
            hash = file['hash'],
            pattern_hash = file['patternhash'],
            license = license,
            create_date = file['date'],
            update_date = file['timestamp'],
        )

        # Generate song stats
        stats = SongStats.objects.create(
            song = song,
            downloads = file['hits'],
            total_comments = file['comment_total'],
            average_comment_score = file['comment_score'],
            total_reviews = file['review_total'],
            average_review_score = file['review_score'],
        )

        # Associate with user?
        return {'song': song, 'stats': stats}

    def post(self, request):
        form = CsvUploadForm(request.POST)
        if form.is_valid:
            uploaded_csv = request.FILES['csv_file'].read()
            file_data = uploaded_csv.decode("utf-8")

            json_data = json.loads(file_data)
            user_data = json_data['users']
            song_data = json_data['files']
            mapping_data = json_data['file_mappings']

            users = []
            profiles = []
            artists = []
            songs = []
            song_stats = []

            for item in user_data:
                values = self.generate_user(item)
                users.append(values['user'])
                profiles.append(values['profile'])
                artists.append(values['artist'])

            for item in song_data:
                values = self.generate_songs(item)
                songs.append(values['song'])
                song_stats.append(values['stats'])

            for item in mapping_data:
                filtered_artists = [x for x in artists if x.legacy_id == item['artist']]
                filtered_songs = [x for x in songs if x.filename == item['filename']]

                if (len(filtered_artists) != 1 or len(filtered_songs) != 1):
                    continue
                
                artist = filtered_artists[0]
                song = filtered_songs[0]

                song.artist_set.add(artist)

        return render(request, 'custom_admin/bulk_upload.html', context={'form': form})
    
    def get(self, request):
        form = CsvUploadForm()
        return render(request, 'custom_admin/bulk_upload.html', context={'form': form})