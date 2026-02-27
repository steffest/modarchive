from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from homepage import legacy_models
from homepage.models import Profile
from uploads.models import RejectedSong

class Command(BaseCommand):
    help = "Migrate the legacy tma_files_rejected table"

    def handle(self, *args, **options):
        rejected_files = legacy_models.TmaFilesRejected.objects.using('legacy').all()

        total = len(rejected_files)
        counter = 0
        print(f"Starting migration of {total} records from tma_files_rejected. This process will populate the rejected songs table.")

        reasons_counter = {}
        other_reasons = []
        batch_size = 1000
        rejected_songs_batch = []

        for rejected_file in rejected_files:
            counter += 1

            if counter % 1000 == 0:
                print(f"Generated {counter} out of {total} tma_files_rejected.")

            try:
                filterer_profile = Profile.objects.get(display_name=rejected_file.filterer)
            except ObjectDoesNotExist:
                filterer_profile = None

            try:
                uploader_profile = Profile.objects.get(id=rejected_file.uploader_uid)
            except ObjectDoesNotExist:
                uploader_profile = None

            if rejected_file.reason == 'The module was rejected because it appeared to be unsupported format/invalid/corrupted.':
                reason = RejectedSong.Reasons.CORRUPTED
            elif rejected_file.reason == 'The module was rejected because it was not of sufficient quality':
                reason = RejectedSong.Reasons.POOR_QUALITY
            elif rejected_file.reason.startswith('The uploaded module is of insufficient quality as it stands'):
                reason = RejectedSong.Reasons.POOR_QUALITY
            elif rejected_file.reason == 'The module was rejected because it seems to rely on VST or some other non-standard instrumentation, or is corrupt. We do not add tracks that do not replay correctly in standalone module players.':
                reason = RejectedSong.Reasons.UNSUPPORTED_FORMAT
            elif rejected_file.reason == 'The module was rejected because is was of poor quality -  it lent towards the tell-tale poor quality sound of a converted MIDI file. We are sorry but we do not accept this quality/form of module.':
                reason = RejectedSong.Reasons.MIDI_CONVERSION
            elif rejected_file.reason == 'This was a fake/test upload':
                reason = RejectedSong.Reasons.TEST_UPLOAD
            elif rejected_file.reason.lower() == 'Dispute - Uploader please check your email.'.lower():
                reason = RejectedSong.Reasons.DISPUTE
            elif rejected_file.reason == 'Too short to be worth adding':
                reason = RejectedSong.Reasons.TOO_SHORT
            elif rejected_file.reason == 'The module was rejected because it was too short to be worth adding':
                reason = RejectedSong.Reasons.TOO_SHORT
            elif rejected_file.reason == 'Dubious content':
                reason = RejectedSong.Reasons.DUBIOUS_CONTENT
            elif rejected_file.reason == 'The module seemed to contain dubious content':
                reason = RejectedSong.Reasons.DUBIOUS_CONTENT
            elif rejected_file.reason == 'Already exists':
                reason = RejectedSong.Reasons.ALREADY_EXISTS
            elif rejected_file.reason == 'We recognise that this module exists on the archive already':
                reason = RejectedSong.Reasons.ALREADY_EXISTS
            elif rejected_file.reason.startswith('TIDY-UP MERGED'):
                reason = RejectedSong.Reasons.ALREADY_EXISTS
            elif rejected_file.reason == 'Too big':
                reason = RejectedSong.Reasons.TOO_BIG
            elif rejected_file.reason == 'The module was larger than the allowed filesize':
                reason = RejectedSong.Reasons.TOO_BIG
            elif rejected_file.reason == 'Unspecified Reason':
                reason = RejectedSong.Reasons.NO_REASON_GIVEN
            elif rejected_file.reason == 'The module was rejected with no specific reason, however it may have broken one of the rules in the upload agreement or in the upload rules':
                reason = RejectedSong.Reasons.NO_REASON_GIVEN
            elif rejected_file.reason == 'Bad filename. Unsuitable for display on the archive.':
                reason = RejectedSong.Reasons.RENAME_REQUIRED
            elif rejected_file.reason == 'Rename the file. Not fit for archiving':
                reason = RejectedSong.Reasons.RENAME_REQUIRED
            elif rejected_file.reason.startswith('The filename'):
                reason = RejectedSong.Reasons.RENAME_REQUIRED
            elif rejected_file.reason == 'Incorrect file extension for the format.':
                reason = RejectedSong.Reasons.INCORRECT_FILE_EXTENSION
            elif rejected_file.reason.startswith('The file extension you use is NOT the correct one for the format of this file.'):
                reason = RejectedSong.Reasons.INCORRECT_FILE_EXTENSION
            elif rejected_file.reason.startswith('The file extension used'):
                reason = RejectedSong.Reasons.INCORRECT_FILE_EXTENSION
            elif rejected_file.reason == 'Tuning issues, samples out of tune - accidental oversight? Try to play your module in XMPlay to see if it plays correctly.':
                reason = RejectedSong.Reasons.TUNING_ISSUES
            elif 'plagiarised' in rejected_file.reason:
                reason = RejectedSong.Reasons.PLAGIARISM
            elif rejected_file.reason == 'Reason unavailable because this is not yet screened by the new system, so the reason is unknown':
                reason = RejectedSong.Reasons.UNKNOWN
            elif 'this module already exists on the archive' in rejected_file.reason:
                reason = RejectedSong.Reasons.ALREADY_EXISTS
            elif 'has been removed from the archive due to problems with the file' in rejected_file.reason:
                reason = RejectedSong.Reasons.CORRUPTED
            elif 'poor quality' in rejected_file.reason:
                reason = RejectedSong.Reasons.POOR_QUALITY
            else:
                other_reasons.append(rejected_file.reason)
                reason = RejectedSong.Reasons.OTHER

            message = rejected_file.reason
            hash_code = rejected_file.hash
            date_rejected = rejected_file.daterejected if rejected_file.daterejected else timezone.now()
            is_temporary = True if rejected_file.hash == 'NOT PERMANENT' else False

            reasons_counter[reason] = reasons_counter.get(reason, 0) + 1

            rejected_songs_batch.append(
                RejectedSong(
                    reason=reason,
                    message=message,
                    is_temporary=is_temporary,
                    rejected_by=filterer_profile,
                    rejected_date=date_rejected,
                    filename=rejected_file.filename,
                    filename_unzipped=rejected_file.filename,
                    title='',
                    format='',
                    file_size=None,
                    channels=None,
                    instrument_text='',
                    comment_text='',
                    hash=hash_code,
                    pattern_hash='',
                    artist_from_file='',
                    uploader_profile=uploader_profile,
                    uploader_ip_address='',
                    is_by_uploader=False,
                    create_date=date_rejected
                )
            )

            # Flush batch when reaching batch_size or end of loop
            if len(rejected_songs_batch) >= batch_size:
                RejectedSong.objects.bulk_create(rejected_songs_batch)
                print(f"Inserted {counter} records out of {total}.")
                rejected_songs_batch = []

        # Flush remaining records in the batch
        if rejected_songs_batch:
            RejectedSong.objects.bulk_create(rejected_songs_batch)
            print(f"Inserted final {len(rejected_songs_batch)} records.")

        print(f"\nCompleted migration of {total} records.")
        print("\nReason breakdown:")
        for reason, count in sorted(reasons_counter.items()):
            print(f"  {reason}: {count}")

        if other_reasons:
            print(f"\nFound {len(set(other_reasons))} unique 'other' reasons:")
            for reason in sorted(set(other_reasons)):
                print(f"  - {reason}")
