from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from homepage import legacy_models
from homepage.models import Profile
from interactions.models import LegacyReview
from songs.models import Song
from .disable_signals import DisableSignals

class Command(BaseCommand):
    help = "Migrate the legacy reviews table from TmaReviews to LegacyReview"

    def handle(self, *args, **options):
        with DisableSignals():
            reviews_queryset = legacy_models.TmaReviews.objects.using('legacy').all()
            total = reviews_queryset.count()

            print(f"Starting migration of {total} reviews.")
            print("Building lookup dictionaries...")

            # Pre-build lookup dictionaries for efficient access (no foreign keys in legacy DB)
            profile_lookup = self.build_profile_lookup()
            song_lookup = self.build_song_lookup()

            print(f"Built lookup dictionaries: {len(profile_lookup)} profiles, {len(song_lookup)} songs")

            batch_size = 1000
            reviews_to_create = []

            counter = 0
            skipped_no_profile = 0
            skipped_no_song = 0
            successful_reviews = 0

            print("Processing reviews...")

            # Process in batches for better performance
            for review in reviews_queryset.iterator(chunk_size=batch_size):
                counter += 1

                review_data = self.prepare_review_data(review, profile_lookup, song_lookup)

                if review_data is not None:
                    reviews_to_create.append(review_data)
                    successful_reviews += 1
                else:
                    # Track skipped records
                    if not self.is_valid_profile(review.userid, profile_lookup):
                        skipped_no_profile += 1
                    if not self.is_valid_song(review.moduleid, song_lookup):
                        skipped_no_song += 1

                # Bulk create when batch is full or at the end
                if len(reviews_to_create) >= batch_size or counter == total:
                    if reviews_to_create:
                        self.bulk_create_batch(reviews_to_create)

                    if counter % 5000 == 0 or counter == total:
                        print(f"Processed {counter} out of {total} reviews. "
                              f"Successful: {successful_reviews}, "
                              f"Skipped (no profile): {skipped_no_profile}, "
                              f"Skipped (no song): {skipped_no_song}")

                    # Clear batch
                    reviews_to_create = []

            print(f"Migration complete! Processed {counter} reviews")
            print(f"  Successful reviews: {successful_reviews}")
            print(f"  Skipped due to missing profile: {skipped_no_profile}")
            print(f"  Skipped due to missing song: {skipped_no_song}")

            # Show percentage of successful processing
            if counter > 0:
                success_rate = (successful_reviews / counter) * 100
                print(f"  Success rate: {success_rate:.1f}%")

    def build_profile_lookup(self):
        """Build a dictionary mapping legacy profile ID to Profile objects for fast lookup"""
        print("Building profile lookup dictionary...")
        profile_lookup = {}

        # Get all profiles with their legacy IDs
        for profile in Profile.objects.all().iterator(chunk_size=1000):
            if profile.legacy_id is not None:
                profile_lookup[profile.legacy_id] = profile

        return profile_lookup

    def build_song_lookup(self):
        """Build a dictionary mapping legacy song ID to Song objects for fast lookup"""
        print("Building song lookup dictionary...")
        song_lookup = {}

        # Get all songs with their legacy IDs
        for song in Song.objects.all().iterator(chunk_size=1000):
            if song.legacy_id is not None:
                song_lookup[song.legacy_id] = song

        return song_lookup

    def is_valid_profile(self, userid, profile_lookup):
        """Check if profile ID exists in lookup"""
        return userid and userid in profile_lookup

    def is_valid_song(self, moduleid, song_lookup):
        """Check if song ID exists in lookup"""
        return moduleid and moduleid in song_lookup

    def prepare_review_data(self, review, profile_lookup, song_lookup):
        """Prepare LegacyReview data object for bulk creation"""

        # Handle profile lookup (no referential integrity in legacy DB)
        if not review.userid or review.userid not in profile_lookup:
            print(f"Could not find profile for userid {review.userid} (review id: {getattr(review, 'id', 'unknown')})")
            return None  # Skip this record

        profile = profile_lookup[review.userid]

        # Handle song lookup (no referential integrity in legacy DB)
        if not review.moduleid or review.moduleid not in song_lookup:
            print(f"Could not find song for moduleid {review.moduleid} (review id: {getattr(review, 'id', 'unknown')})")
            return None  # Skip this record

        song = song_lookup[review.moduleid]

        # Create LegacyReview object
        legacy_review = LegacyReview(
            profile=profile,
            song=song,
            pending=bool(review.pending),
            pending_screening=bool(review.pending_screening),
            rejection_text=review.rejection_text,
            incomplete=bool(review.incomplete),
            impression_score=int(review.review_r1) if review.review_r1 else 0,
            impression_text=review.review_1,
            technique_score=int(review.review_r2) if review.review_r2 else 0,
            technique_text=review.review_2,
            development_score=int(review.review_r3) if review.review_r3 else 0,
            development_text=review.review_3,
            creativity_score=int(review.review_r4) if review.review_r4 else 0,
            creativity_text=review.review_4,
            enjoyment_score=int(review.review_r5) if review.review_r5 else 0,
            enjoyment_text=review.review_5,
            additional_text=review.review_6,
            create_date=review.date
        )

        return legacy_review

    def bulk_create_batch(self, reviews_to_create):
        """Bulk create reviews"""

        with transaction.atomic():
            try:
                # Bulk create reviews
                try:
                    created_reviews = LegacyReview.objects.bulk_create(reviews_to_create)
                    print(f"  Created {len(created_reviews)} reviews")
                except Exception as review_error:
                    print(f"Bulk review creation failed: {review_error}")
                    # Fall back to individual creation
                    successful_reviews = 0
                    for review in reviews_to_create:
                        try:
                            LegacyReview.objects.create(
                                profile=review.profile,
                                song=review.song,
                                pending=review.pending,
                                pending_screening=review.pending_screening,
                                rejection_text=review.rejection_text,
                                incomplete=review.incomplete,
                                impression_score=review.impression_score,
                                impression_text=review.impression_text,
                                technique_score=review.technique_score,
                                technique_text=review.technique_text,
                                development_score=review.development_score,
                                development_text=review.development_text,
                                creativity_score=review.creativity_score,
                                creativity_text=review.creativity_text,
                                enjoyment_score=review.enjoyment_score,
                                enjoyment_text=review.enjoyment_text,
                                additional_text=review.additional_text,
                                create_date=review.create_date
                            )
                            successful_reviews += 1
                        except IntegrityError as e:
                            print(f"Failed to create review for profile {review.profile.id} and song {review.song.id}: {e}")
                        except Exception as e:
                            print(f"Unexpected error creating review: {e}")
                    print(f"  Created {successful_reviews} reviews individually")

            except Exception as e:
                print(f"Error during bulk creation: {str(e)}")
                import traceback
                traceback.print_exc()
