from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.db.models import F
from collections import defaultdict

from homepage import legacy_models
from homepage.models import Profile
from interactions.models import Favorite
from songs.models import Song
from .disable_signals import DisableSignals

class Command(BaseCommand):
    help = "Migrate the legacy favorites table"

    def handle(self, *args, **options):
        with DisableSignals():
            # Use iterator() to avoid loading all records into memory
            favorites_queryset = legacy_models.TmaFavourites.objects.using('legacy').all()
            total = favorites_queryset.count()
            
            print(f"Starting migration of {total} favorites.")
            print("Building validation lookup sets...")
            
            # Pre-build lookup sets for efficient validation (no foreign keys in legacy DB)
            valid_profile_ids = self.build_valid_profile_ids()
            valid_song_ids = self.build_valid_song_ids()
            
            print(f"Built validation sets: {len(valid_profile_ids)} profiles, {len(valid_song_ids)} songs")
            
            batch_size = 1000
            favorites_to_create = []
            song_favorite_counts = defaultdict(int)  # song_id -> count increment
            
            counter = 0
            skipped_no_profile = 0
            skipped_no_song = 0
            successful_favorites = 0
            
            print("Processing favorites...")
            
            # Process in batches for better performance
            for fave in favorites_queryset.iterator(chunk_size=batch_size):
                counter += 1
                
                # Validate profile ID exists (handle referential integrity issues)
                profile_id = fave.userid if fave.userid else None
                if not profile_id or profile_id not in valid_profile_ids:
                    skipped_no_profile += 1
                    if skipped_no_profile <= 10:  # Show first 10 warnings
                        print(f"Profile does not exist for userid {fave.userid} (favorite id: {getattr(fave, 'id', 'unknown')})")
                    continue
                
                # Validate song ID exists (handle referential integrity issues)
                song_id = fave.moduleid if fave.moduleid else None
                if not song_id or song_id not in valid_song_ids:
                    skipped_no_song += 1
                    if skipped_no_song <= 10:  # Show first 10 warnings
                        print(f"Song does not exist for moduleid {fave.moduleid} (favorite id: {getattr(fave, 'id', 'unknown')})")
                    continue
                
                # Create Favorite object with direct ID assignment
                favorite = Favorite(
                    profile_id=profile_id,  # Direct ID assignment
                    song_id=song_id        # Direct ID assignment
                )
                favorites_to_create.append(favorite)
                
                # Track favorite count increments for each song
                song_favorite_counts[song_id] += 1
                successful_favorites += 1
                
                # Bulk create when batch is full or at the end
                if len(favorites_to_create) >= batch_size or counter == total:
                    if favorites_to_create:
                        self.bulk_create_batch(favorites_to_create, song_favorite_counts)
                    
                    if counter % 5000 == 0 or counter == total:
                        print(f"Processed {counter} out of {total} favorites. "
                              f"Successful: {successful_favorites}, "
                              f"Skipped (no profile): {skipped_no_profile}, "
                              f"Skipped (no song): {skipped_no_song}")
                    
                    # Clear batches
                    favorites_to_create = []
                    song_favorite_counts = defaultdict(int)
            
            print(f"Migration complete! Processed {counter} favorites")
            print(f"  Successful favorites: {successful_favorites}")
            print(f"  Skipped due to missing profile: {skipped_no_profile}")
            print(f"  Skipped due to missing song: {skipped_no_song}")
            
            # Show percentage of successful processing
            if counter > 0:
                success_rate = (successful_favorites / counter) * 100
                print(f"  Success rate: {success_rate:.1f}%")

    def build_valid_profile_ids(self):
        """Build a set of valid profile IDs for efficient validation"""
        print("Building valid profile IDs set...")
        valid_ids = set()
        
        # Get all profile IDs that exist
        for profile_id in Profile.objects.values_list('id', flat=True).iterator(chunk_size=1000):
            if profile_id is not None:
                valid_ids.add(profile_id)
        
        return valid_ids

    def build_valid_song_ids(self):
        """Build a set of valid song IDs for efficient validation"""
        print("Building valid song IDs set...")
        valid_ids = set()
        
        # Get all song IDs that exist
        for song_id in Song.objects.values_list('id', flat=True).iterator(chunk_size=1000):
            if song_id is not None:
                valid_ids.add(song_id)
        
        return valid_ids

    def bulk_create_batch(self, favorites_to_create, song_favorite_counts):
        """Bulk create favorites and update song favorite counts"""
        
        with transaction.atomic():
            try:
                # Bulk create favorites
                try:
                    created_favorites = Favorite.objects.bulk_create(favorites_to_create)
                    print(f"  Created {len(created_favorites)} favorites")
                except Exception as favorite_error:
                    print(f"Bulk favorite creation failed: {favorite_error}")
                    # Fall back to individual creation
                    successful_favorites = 0
                    for favorite in favorites_to_create:
                        try:
                            Favorite.objects.create(
                                profile_id=favorite.profile_id,
                                song_id=favorite.song_id
                            )
                            successful_favorites += 1
                        except IntegrityError as e:
                            print(f"Failed to create favorite for profile {favorite.profile_id} and song {favorite.song_id}: {e}")
                        except Exception as e:
                            print(f"Unexpected error creating favorite: {e}")
                    print(f"  Created {successful_favorites} favorites individually")
                
                # Bulk update favorite counts for songs
                if song_favorite_counts:
                    self.bulk_update_favorite_counts(song_favorite_counts)
                    
            except Exception as e:
                print(f"Error during bulk creation: {str(e)}")
                import traceback
                traceback.print_exc()

    def bulk_update_favorite_counts(self, song_favorite_counts):
        """Efficiently update favorite counts for songs"""
        try:
            updated_count = 0
            failed_count = 0
            
            # Get all relevant songs and their stats
            song_ids = list(song_favorite_counts.keys())
            
            # Update counts in batches to avoid large queries
            batch_size = 100
            for i in range(0, len(song_ids), batch_size):
                batch_song_ids = song_ids[i:i + batch_size]
                
                try:
                    # Update song stats for this batch
                    for song_id in batch_song_ids:
                        increment = song_favorite_counts[song_id]
                        
                        # Try to get the song and update its stats
                        try:
                            song = Song.objects.get(id=song_id)
                            stats = song.get_stats()
                            stats.total_favorites = F('total_favorites') + increment
                            stats.save(update_fields=['total_favorites'])
                            updated_count += 1
                        except Exception as e:
                            failed_count += 1
                            if failed_count <= 5:  # Show first few failures
                                print(f"Failed to update favorite count for song {song_id}: {e}")
                
                except Exception as batch_error:
                    print(f"Error updating favorite counts for batch: {batch_error}")
                    failed_count += len(batch_song_ids)
            
            print(f"  Updated favorite counts for {updated_count} songs")
            if failed_count > 5:
                print(f"  Failed to update counts for {failed_count} songs")
                
        except Exception as e:
            print(f"Error in bulk_update_favorite_counts: {e}")
