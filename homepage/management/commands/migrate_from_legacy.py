from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import time


def _format_seconds(seconds: float) -> str:
    """Format seconds as M:SS"""
    total = int(round(seconds))
    minutes = total // 60
    secs = total % 60
    return f"{minutes}:{secs:02d}"

class Command(BaseCommand):
    help = (
        "Runs the recommended sequence of legacy migration management commands in order.\n"
        "Use --stop-on-error to stop execution on the first failing command."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--stop-on-error",
            action="store_true",
            dest="stop_on_error",
            help="Stop execution if any command raises an error.",
        )

    def handle_error(self, e: CommandError | Exception, name, results, elapsed: float, status: str, message: str):
        error_msg = str(e)
        self.stderr.write(self.style.ERROR(message))
        results.append({"name": name, "elapsed": elapsed, "status": status, "error": error_msg})
        # print timing for this command
        self.stdout.write(self.style.NOTICE(f"Time for {name}: {_format_seconds(elapsed)}"))

    def handle(self, *args, **options):
        stop_on_error = options.get("stop_on_error", False)

        commands = [
            ("create_groups", {}),
            ("migrate_users", {}),
            ("migrate_files", {}),
            ("migrate_artist_mappings_real", {}),
            ("migrate_favorites", {}),
            ("migrate_comments", {}),
            ("migrate_files_new", {}),
            ("migrate_nominations", {}),
            ("migrate_files_uploader", {}),
            ("migrate_redirects", {}),
            ("migrate_rejected_files", {}),
            ("migrate_messages", {}),
            ("migrate_reviews", {}),
            # Optional/extra commands
            ("update_artist_search_indexes", {"all": True}),
            ("update_song_search_indexes", {"all": True}),
            # BBCode conversions (run separately for each target)
            ("convert_bbcode", {"comments": True}),
            ("convert_bbcode", {"artist_comments": True}),
            ("convert_bbcode", {"profile_blurbs": True}),
            ("convert_bbcode", {"messages": True}),
            # Recalculate stats (can be run separately or after all migrations are done)
            ("recalculate_stats", {}),
        ]

        results = []  # list of dicts: {name, elapsed, status, error}
        overall_start = time.monotonic()

        for name, kwargs in commands:
            self.stdout.write(self.style.MIGRATE_HEADING(f"Running {name} with options {kwargs}"))
            start = time.monotonic()
            status = "success"
            error_msg = None
            try:
                # call_command will raise CommandError if the command signals a problem
                call_command(name, **kwargs)
            except CommandError as e:
                elapsed = time.monotonic() - start
                self.handle_error(e, name, results, elapsed, "failed", f"Command '{name}' failed: {e}")
                if stop_on_error:
                    break
                else:
                    # continue to next command
                    continue
            except Exception as e:
                elapsed = time.monotonic() - start
                self.handle_error(e, name, results, elapsed, "error", f"Unexpected error running '{name}': {e}")
                if stop_on_error:
                    break
                else:
                    continue

            # If we got here the command succeeded
            elapsed = time.monotonic() - start
            results.append({"name": name, "elapsed": elapsed, "status": status, "error": error_msg})
            self.stdout.write(self.style.NOTICE(f"Time for {name}: {_format_seconds(elapsed)}"))

        total_elapsed = time.monotonic() - overall_start

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_LABEL("Legacy migration timing summary:"))
        for r in results:
            line = f"{r['name']}: {r['status'].upper():7}  {_format_seconds(r['elapsed'])}"
            self.stdout.write(line)
            if r.get("error"):
                self.stdout.write(f"    Error: {r['error']}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Total elapsed time: {_format_seconds(total_elapsed)}"))
