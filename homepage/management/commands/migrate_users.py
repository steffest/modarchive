from django.core.management.base import BaseCommand
from django.core.management import CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.contrib.auth.models import Group
from homepage import legacy_models
from homepage.models import Profile
from artists.models import Artist
from .disable_signals import DisableSignals

User = get_user_model()

# Recommended order for migration:
# 0. --create_groups
# 1. --migrate_users
# 2. --migrate_files
# 3. --migrate_artist_mappings_real
# 4. --migrate_favorites
# 5. --migrate_comments
# 6. --migrate_files_new
# 7. --migrate_nominations
# 8. --migrate_files_uploader
# 9. --migrate_redirects
# 10. --migrate_rejected_files
#
# --update_artist_search_indexes --all
# --update_song_search_indexes --all
#
# --convert_bbcode --comments
# --convert_bbcode --artist_comments
# --convert_bbcode --profile_blurbs
class Command(BaseCommand):
    help = "Migrates the legacy users table"

    def handle(self, *args, **options):
        with DisableSignals():
            # Use iterator() to avoid loading all records into memory
            users_queryset = legacy_models.Users.objects.using('legacy').all().order_by('userid')
            total = users_queryset.count()

            try:
                standard_group = Group.objects.get(name='Standard')
                screener_group = Group.objects.get(name='Screeners')
                artist_group = Group.objects.get(name='Artists')
                admin_group = Group.objects.get(name='Admins')
            except Group.DoesNotExist as e:
                raise CommandError(f"Missing required group: {e}") from e

            print(f"Starting migrations of {total} users. This process will create all user, profile, and artist objects.")

            batch_size = 1000
            users_to_create = []
            profiles_to_create = []
            artists_to_create = []
            
            # For tracking group memberships after bulk creation
            admin_user_indices = []
            screener_user_indices = []
            artist_user_indices = []
            
            counter = 0

            # Process in batches for better performance
            for legacy_user in users_queryset.iterator(chunk_size=batch_size):
                counter += 1

                user_data, profile_data, artist_data = self.prepare_user_data(legacy_user)
                
                if user_data:  # Only process if user creation data is valid
                    current_user_index = len(users_to_create)
                    users_to_create.append(user_data)
                    
                    # Always create a profile for each user
                    if profile_data:
                        profiles_to_create.append(profile_data)
                    else:
                        print(f"Warning: No profile data for user {legacy_user.username}")
                    
                    # Track group memberships by index
                    if legacy_user.cred_admin == "1":
                        admin_user_indices.append(current_user_index)
                    if legacy_user.cred_filterer == "1":
                        screener_user_indices.append(current_user_index)
                    
                    # Only create artist if user is marked as artist
                    if artist_data:
                        artists_to_create.append(artist_data)
                        artist_user_indices.append(current_user_index)

                # Bulk create when batch is full or at the end
                if len(users_to_create) >= batch_size or counter == total:
                    if users_to_create:  # Only process if we have users to create
                        self.bulk_create_batch(
                            users_to_create, profiles_to_create, artists_to_create,
                            admin_user_indices, screener_user_indices, artist_user_indices,
                            admin_group, screener_group, artist_group, standard_group
                        )

                    print(f"Generated {counter} out of {total} from the legacy users table.")
                    
                    # Clear batches
                    users_to_create = []
                    profiles_to_create = []
                    artists_to_create = []
                    admin_user_indices = []
                    screener_user_indices = []
                    artist_user_indices = []

    def prepare_user_data(self, legacy_user):
        """Prepare User, Profile, and Artist data objects for bulk creation"""
        username = legacy_user.username
        password = self.get_password_with_hashing_algorithm(legacy_user.profile_password)
        email = legacy_user.profile_email
        is_staff = True if legacy_user.cred_admin == "1" else False
        date_joined = legacy_user.date
        enable_notifications = True if legacy_user.profile_notifications == 1 else False
        enable_shoutwall_notifications = True if legacy_user.profile_shout_notifications == 1 else False
        enable_shoutwall = True if legacy_user.profile_shoutwall_status == 1 else False
        website = legacy_user.profile_web

        # Create User object (no ID assignment - let Django auto-assign)
        user_data = User(
            username=username,
            password=password,
            email=email,
            date_joined=date_joined,
            is_staff=is_staff
        )

        # Create Profile object with explicit ID to preserve legacy user ID  
        profile_data = Profile(
            id=legacy_user.userid,  # Preserve legacy ID for Profile
            display_name=legacy_user.profile_fullname,
            blurb=legacy_user.profile_blurb,
            create_date=legacy_user.date,
            update_date=legacy_user.lastlogin,
            legacy_id=legacy_user.userid,
            enable_notifications=enable_notifications,
            enable_shoutwall_notifications=enable_shoutwall_notifications,
            enable_shoutwall=enable_shoutwall,
            website=website
            # user will be set after bulk user creation
        )

        # Create Artist object if user is an artist, with explicit ID
        artist_data = None
        if legacy_user.cred_artist == "1":
            artist_data = Artist(
                id=legacy_user.userid,  # Preserve legacy ID for Artist
                legacy_id=legacy_user.userid,
                name=legacy_user.profile_fullname,
                create_date=legacy_user.date,
                update_date=legacy_user.lastlogin
                # user and profile will be set after bulk creation
            )

        return user_data, profile_data, artist_data

    def bulk_create_batch(self, users_to_create, profiles_to_create, artists_to_create,
                         admin_user_indices, screener_user_indices, artist_user_indices,
                         admin_group, screener_group, artist_group, standard_group):
        """Bulk create users, profiles, and artists with proper relationships and group assignments"""
        
        with transaction.atomic():
            try:
                print(f"Bulk creating batch: {len(users_to_create)} users, {len(profiles_to_create)} profiles, {len(artists_to_create)} artists")
                
                # Bulk create users first - remove ignore_conflicts to get PKs back
                try:
                    created_users = User.objects.bulk_create(users_to_create)
                    successful_users = created_users  # All should have PKs now
                    print(f"Successfully created {len(successful_users)} users")
                    print(f"First user PK: {successful_users[0].pk if successful_users else 'None'}")  # Debug output
                except Exception as bulk_error:
                    print(f"Bulk user creation failed: {bulk_error}")
                    # Fall back to individual creation
                    successful_users = []
                    for user_data in users_to_create:
                        try:
                            created_user = User.objects.create(
                                username=user_data.username,
                                password=user_data.password,
                                email=user_data.email,
                                date_joined=user_data.date_joined,
                                is_staff=user_data.is_staff
                            )
                            successful_users.append(created_user)
                        except Exception as e:
                            print(f"Failed to create user {user_data.username}: {e}")
                    
                    print(f"Created {len(successful_users)} users individually")
                
                # Update profiles with the created user instances
                # Each profile corresponds to a user at the same index
                for i, profile in enumerate(profiles_to_create):
                    if i < len(successful_users):
                        profile.user = successful_users[i]
                    else:
                        print(f"Warning: Profile {i} has no corresponding user")
                        break
                
                # Bulk create profiles
                if profiles_to_create:
                    try:
                        created_profiles = Profile.objects.bulk_create(profiles_to_create)
                        successful_profiles = created_profiles  # All should have PKs now
                        print(f"Successfully created {len(successful_profiles)} profiles")
                    except Exception as profile_error:
                        print(f"Bulk profile creation failed: {profile_error}")
                        # Fall back to individual creation
                        successful_profiles = []
                        for i, profile_data in enumerate(profiles_to_create):
                            if i < len(successful_users):
                                try:
                                    created_profile = Profile.objects.create(
                                        id=profile_data.id,
                                        user=profile_data.user,
                                        display_name=profile_data.display_name,
                                        blurb=profile_data.blurb,
                                        create_date=profile_data.create_date,
                                        update_date=profile_data.update_date,
                                        legacy_id=profile_data.legacy_id
                                    )
                                    successful_profiles.append(created_profile)
                                except Exception as e:
                                    print(f"Failed to create profile for user {profile_data.user.username}: {e}")
                        print(f"Created {len(successful_profiles)} profiles individually")
                else:
                    successful_profiles = []
                
                # Update artists with the created user and profile instances
                # Artists correspond to specific users based on artist_user_indices
                for i, artist in enumerate(artists_to_create):
                    if i < len(artist_user_indices):
                        user_index = artist_user_indices[i]
                        if user_index < len(successful_users) and user_index < len(successful_profiles):
                            artist.user = successful_users[user_index]
                            artist.profile = successful_profiles[user_index]
                        else:
                            print(f"Warning: Artist {i} references invalid user/profile index {user_index}")
                            # Remove this artist from the list
                            artists_to_create[i] = None
                
                # Filter out None artists
                valid_artists = [artist for artist in artists_to_create if artist is not None]
                
                # Bulk create artists
                if valid_artists:
                    try:
                        created_artists = Artist.objects.bulk_create(valid_artists)
                        successful_artists = created_artists  # All should have PKs now
                        print(f"Successfully created {len(successful_artists)} artists")
                    except Exception as artist_error:
                        print(f"Bulk artist creation failed: {artist_error}")
                        # Fall back to individual creation
                        successful_artists = []
                        for artist_data in valid_artists:
                            try:
                                created_artist = Artist.objects.create(
                                    id=artist_data.id,
                                    user=artist_data.user,
                                    profile=artist_data.profile,
                                    legacy_id=artist_data.legacy_id,
                                    name=artist_data.name,
                                    create_date=artist_data.create_date,
                                    update_date=artist_data.update_date
                                )
                                successful_artists.append(created_artist)
                            except Exception as e:
                                print(f"Failed to create artist {artist_data.name}: {e}")
                                # Try with modified name
                                try:
                                    created_artist = Artist.objects.create(
                                        id=artist_data.id,
                                        user=artist_data.user,
                                        profile=artist_data.profile,
                                        legacy_id=artist_data.legacy_id,
                                        name=artist_data.name + "_1",
                                        create_date=artist_data.create_date,
                                        update_date=artist_data.update_date
                                    )
                                    successful_artists.append(created_artist)
                                except Exception as e2:
                                    print(f"Failed to create artist {artist_data.name}_1: {e2}")
                        print(f"Created {len(successful_artists)} artists individually")
                
                # Handle group assignments efficiently
                self.assign_groups_bulk(successful_users, admin_user_indices, screener_user_indices, 
                                      artist_user_indices, admin_group, screener_group, 
                                      artist_group, standard_group)
                
            except Exception as e:
                print(f"Error during bulk creation: {str(e)}")
                import traceback
                traceback.print_exc()
                # Fall back to individual creation for this batch
                self.fallback_individual_creation(users_to_create, profiles_to_create, artists_to_create,
                                                admin_user_indices, screener_user_indices, artist_user_indices,
                                                admin_group, screener_group, artist_group, standard_group)

    def assign_groups_bulk(self, created_users, admin_user_indices, screener_user_indices,
                          artist_user_indices, admin_group, screener_group, artist_group, standard_group):
        """Efficiently assign group memberships to created users"""
        
        # Add all users to standard group
        standard_group.user_set.add(*created_users)
        
        # Add specific users to admin group
        if admin_user_indices:
            admin_users = [created_users[i] for i in admin_user_indices if i < len(created_users)]
            if admin_users:
                admin_group.user_set.add(*admin_users)
        
        # Add specific users to screener group
        if screener_user_indices:
            screener_users = [created_users[i] for i in screener_user_indices if i < len(created_users)]
            if screener_users:
                screener_group.user_set.add(*screener_users)
        
        # Add specific users to artist group
        if artist_user_indices:
            artist_users = [created_users[i] for i in artist_user_indices if i < len(created_users)]
            if artist_users:
                artist_group.user_set.add(*artist_users)

    def fallback_individual_creation(self, users_to_create, profiles_to_create, artists_to_create,
                                   admin_user_indices, screener_user_indices, artist_user_indices,
                                   admin_group, screener_group, artist_group, standard_group):
        """Fallback to individual creation if bulk creation fails"""
        print("Falling back to individual creation for this batch...")
        
        for i, user_data in enumerate(users_to_create):
            try:
                # Create user individually
                new_user = User.objects.create(
                    username=user_data.username,
                    password=user_data.password,
                    email=user_data.email,
                    date_joined=user_data.date_joined,
                    is_staff=user_data.is_staff
                )
                
                # Add to standard group
                new_user.groups.add(standard_group)
                
                # Add to special groups if needed
                if i in admin_user_indices:
                    new_user.groups.add(admin_group)
                if i in screener_user_indices:
                    new_user.groups.add(screener_group)
                
                # Create profile if we have one
                if i < len(profiles_to_create):
                    profile_data = profiles_to_create[i]
                    try:
                        new_profile = Profile.objects.create(
                            id=profile_data.id,
                            user=new_user,
                            display_name=profile_data.display_name,
                            blurb=profile_data.blurb,
                            create_date=profile_data.create_date,
                            update_date=profile_data.update_date,
                            legacy_id=profile_data.legacy_id
                        )
                        
                        # Create artist if this user should be an artist
                        if i in artist_user_indices and i < len(artists_to_create):
                            artist_data = artists_to_create[i]
                            try:
                                Artist.objects.create(
                                    id=artist_data.id,
                                    user=new_user,
                                    profile=new_profile,
                                    legacy_id=artist_data.legacy_id,
                                    name=artist_data.name,
                                    create_date=artist_data.create_date,
                                    update_date=artist_data.update_date
                                )
                                new_user.groups.add(artist_group)
                            except IntegrityError:
                                # Try with modified name
                                try:
                                    Artist.objects.create(
                                        id=artist_data.id,
                                        user=new_user,
                                        profile=new_profile,
                                        legacy_id=artist_data.legacy_id,
                                        name=artist_data.name + "_1",
                                        create_date=artist_data.create_date,
                                        update_date=artist_data.update_date
                                    )
                                    new_user.groups.add(artist_group)
                                except IntegrityError as e:
                                    print(f"Could not create artist for user {new_user.username}: {str(e)}")
                    
                    except IntegrityError as e:
                        print(f"Could not create profile for user {new_user.username}: {str(e)}")
                
            except IntegrityError as e:
                print(f"Could not create user {user_data.username}: {str(e)}")

    def generate_user(self, legacy_user, admin_group: Group, screener_group: Group):
        # Legacy method - kept for compatibility but not used in optimized version
        username = legacy_user.username
        password = self.get_password_with_hashing_algorithm(legacy_user.profile_password)
        email = legacy_user.profile_email
        is_staff = True if legacy_user.cred_admin == "1" else False
        date_joined = legacy_user.date

        try:
            new_user = User.objects.create(username = username, password = password, email = email, date_joined = date_joined, is_staff = is_staff)
            if is_staff:
                new_user.groups.add(admin_group)
            if legacy_user.cred_filterer == "1":
                new_user.groups.add(screener_group)
            return new_user
        except IntegrityError as e:
            print(f"Could not create user {username} due to IntegrityError {str(e)}")
            return None

    def generate_profile(self, legacy_user, new_user):
        # Legacy method - kept for compatibility but not used in optimized version
        try:
            return Profile.objects.create(
                user = new_user,
                display_name = legacy_user.profile_fullname,
                blurb = legacy_user.profile_blurb,
                create_date = legacy_user.date,
                update_date = legacy_user.lastlogin,
                legacy_id = legacy_user.userid
            )
        except IntegrityError as e:
            print(f"Could not create profile for user {new_user.username} due to IntegrityError {str(e)}")
            return None

    def generate_artist(self, legacy_user, new_user, profile):
        # Legacy method - kept for compatibility but not used in optimized version
        try:
            return Artist.objects.create(
                user = new_user,
                profile = profile,
                legacy_id = legacy_user.userid,
                name = legacy_user.profile_fullname,
                create_date = legacy_user.date,
                update_date = legacy_user.lastlogin
            )
        except IntegrityError as e:
            print(f"Could not create artist for user {new_user.username} due to IntegrityError {str(e)}")
            print(f"Trying again with username {legacy_user.profile_fullname}_1 instead")

            return Artist.objects.create(
                user = new_user,
                profile = profile,
                legacy_id = legacy_user.userid,
                name = legacy_user.profile_fullname + "_1",
                create_date = legacy_user.date,
                update_date = legacy_user.lastlogin
            )

    def get_password_with_hashing_algorithm(self, password):
        """Convert legacy password format to Django-compatible format"""
        if password.startswith("$2y"):
            return "bcrypt$" + password

        if password:
            return "hmac$" + password

        return password
