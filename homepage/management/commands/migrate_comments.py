from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from homepage import legacy_models
from homepage.models import Profile
from interactions.models import Comment
from songs.models import Song
from .disable_signals import DisableSignals

class Command(BaseCommand):
    help = "Migrate the legacy comments table"

    def handle(self, *args, **options):
        with DisableSignals():
            # Use iterator() to avoid loading all records into memory
            comments_queryset = legacy_models.TmaComments.objects.using('legacy').all()
            total = comments_queryset.count()
            
            print(f"Starting migration of {total} comments.")
            print("Building lookup dictionaries...")
            
            # Pre-build lookup dictionaries for efficient access (no foreign keys in legacy DB)
            profile_lookup = self.build_profile_lookup()
            song_lookup = self.build_song_lookup()
            
            print(f"Built lookup dictionaries: {len(profile_lookup)} profiles, {len(song_lookup)} songs")
            
            batch_size = 1000
            comments_to_create = []
            
            counter = 0
            skipped_no_profile = 0
            skipped_no_song = 0
            successful_comments = 0
            anonymous_comments = 0
            
            print("Processing comments...")
            
            # Process in batches for better performance
            for comment in comments_queryset.iterator(chunk_size=batch_size):
                counter += 1
                
                comment_data = self.prepare_comment_data(comment, profile_lookup, song_lookup)
                
                if comment_data is not None:
                    comments_to_create.append(comment_data)
                    successful_comments += 1
                    
                    # Track anonymous comments
                    if comment_data.profile is None:
                        anonymous_comments += 1
                else:
                    # Track skipped records (already logged in prepare_comment_data)
                    if not self.is_valid_profile(comment.userid, profile_lookup):
                        skipped_no_profile += 1
                    if not self.is_valid_song(comment.moduleid, song_lookup):
                        skipped_no_song += 1
                
                # Bulk create when batch is full or at the end
                if len(comments_to_create) >= batch_size or counter == total:
                    if comments_to_create:
                        self.bulk_create_batch(comments_to_create)
                    
                    if counter % 5000 == 0 or counter == total:
                        print(f"Processed {counter} out of {total} comments. "
                              f"Successful: {successful_comments}, "
                              f"Anonymous: {anonymous_comments}, "
                              f"Skipped (no profile): {skipped_no_profile}, "
                              f"Skipped (no song): {skipped_no_song}")
                    
                    # Clear batch
                    comments_to_create = []
            
            print(f"Migration complete! Processed {counter} comments")
            print(f"  Successful comments: {successful_comments}")
            print(f"  Anonymous comments: {anonymous_comments}")
            print(f"  Skipped due to missing profile: {skipped_no_profile}")
            print(f"  Skipped due to missing song: {skipped_no_song}")
            
            # Show percentage of successful processing
            if counter > 0:
                success_rate = (successful_comments / counter) * 100
                print(f"  Success rate: {success_rate:.1f}%")

    def build_profile_lookup(self):
        """Build a dictionary mapping legacy profile ID to Profile objects for fast lookup"""
        print("Building profile lookup dictionary...")
        profile_lookup = {}
        
        # Get all profiles with their legacy IDs
        for profile in Profile.objects.all().iterator(chunk_size=1000):
            if profile.legacy_id is not None:  # Handle legacy_id = 0 as valid
                profile_lookup[profile.legacy_id] = profile
        
        return profile_lookup

    def build_song_lookup(self):
        """Build a dictionary mapping legacy song ID to Song objects for fast lookup"""
        print("Building song lookup dictionary...")
        song_lookup = {}
        
        # Get all songs with their legacy IDs
        for song in Song.objects.all().iterator(chunk_size=1000):
            if song.legacy_id is not None:  # Handle legacy_id = 0 as valid
                song_lookup[song.legacy_id] = song
        
        return song_lookup

    def is_valid_profile(self, userid, profile_lookup):
        """Check if profile is valid (special handling for userid 1 - anonymous)"""
        if userid == 1:
            return True  # Anonymous comments are allowed
        return userid and userid in profile_lookup

    def is_valid_song(self, moduleid, song_lookup):
        """Check if song ID exists in lookup"""
        return moduleid and moduleid in song_lookup

    def prepare_comment_data(self, comment, profile_lookup, song_lookup):
        """Prepare Comment data object for bulk creation"""
        
        # Handle profile with special case for anonymous comments (no referential integrity in legacy DB)
        profile = None
        if comment.userid and comment.userid != 1:  # userid 1 = anonymous
            if comment.userid in profile_lookup:
                profile = profile_lookup[comment.userid]
            else:
                print(f"Could not find profile for userid {comment.userid} (comment id: {getattr(comment, 'id', 'unknown')})")
                return None  # Skip this record
        # If userid == 1, profile remains None (anonymous comment)
        
        # Handle song lookup (no referential integrity in legacy DB)
        if not comment.moduleid or comment.moduleid not in song_lookup:
            print(f"Could not find song for moduleid {comment.moduleid} (comment id: {getattr(comment, 'id', 'unknown')})")
            return None  # Skip this record
        
        song = song_lookup[comment.moduleid]
        
        # Create Comment object
        comment_obj = Comment(
            profile=profile,  # Can be None for anonymous comments
            song=song,
            text=comment.comment_text,
            rating=comment.comment_rating,
            create_date=comment.comment_date
        )
        
        return comment_obj

    def bulk_create_batch(self, comments_to_create):
        """Bulk create comments"""
        
        with transaction.atomic():
            try:
                # Bulk create comments
                try:
                    created_comments = Comment.objects.bulk_create(comments_to_create)
                    print(f"  Created {len(created_comments)} comments")
                except Exception as comment_error:
                    print(f"Bulk comment creation failed: {comment_error}")
                    # Fall back to individual creation
                    successful_comments = 0
                    for comment in comments_to_create:
                        try:
                            Comment.objects.create(
                                profile=comment.profile,
                                song=comment.song,
                                text=comment.text,
                                rating=comment.rating,
                                create_date=comment.create_date
                            )
                            successful_comments += 1
                        except IntegrityError as e:
                            profile_info = f"profile {comment.profile.id}" if comment.profile else "anonymous"
                            print(f"Failed to create comment for {profile_info} and song {comment.song.id}: {e}")
                        except Exception as e:
                            print(f"Unexpected error creating comment: {e}")
                    print(f"  Created {successful_comments} comments individually")
                    
            except Exception as e:
                print(f"Error during bulk creation: {str(e)}")
                import traceback
                traceback.print_exc()
