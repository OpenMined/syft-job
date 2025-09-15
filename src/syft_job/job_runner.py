import shutil
import time
from typing import List, Set

from .config import SyftJobConfig


class SyftJobRunner:
    """Job runner that monitors inbox folder for new jobs."""

    def __init__(self, config: SyftJobConfig, poll_interval: int = 5):
        """
        Initialize the job runner.

        Args:
            config: SyftJobConfig instance
            poll_interval: How often to check for new jobs (in seconds)
        """
        self.config = config
        self.poll_interval = poll_interval
        self.known_jobs: Set[str] = set()

        # Ensure directory structure exists for the root user
        self._ensure_root_user_directories()

    def _ensure_root_user_directories(self) -> None:
        """Ensure job directory structure exists for the root user."""
        root_email = self.config.email
        job_dir = self.config.get_job_dir(root_email)
        inbox_dir = self.config.get_inbox_dir(root_email)
        approved_dir = self.config.get_approved_dir(root_email)
        done_dir = self.config.get_done_dir(root_email)

        # Create directories if they don't exist
        for directory in [job_dir, inbox_dir, approved_dir, done_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Ensured directory exists: {directory}")

    def _get_jobs_in_inbox(self) -> List[str]:
        """Get list of job names currently in the inbox."""
        inbox_dir = self.config.get_inbox_dir(self.config.email)

        if not inbox_dir.exists():
            return []

        jobs = []
        for item in inbox_dir.iterdir():
            if item.is_dir():
                jobs.append(item.name)

        return jobs

    def _print_new_job(self, job_name: str) -> None:
        """Print information about a new job in the inbox."""
        job_dir = self.config.get_inbox_dir(self.config.email) / job_name

        print(f"\n🔔 NEW JOB DETECTED: {job_name}")
        print(f"📁 Location: {job_dir}")

        # Check if run.sh exists and show first few lines
        run_script = job_dir / "run.sh"
        if run_script.exists():
            try:
                with open(run_script, "r") as f:
                    lines = f.readlines()[:5]  # Show first 5 lines
                print("📝 Script preview:")
                for i, line in enumerate(lines, 1):
                    print(f"   {i}: {line.rstrip()}")
                if len(lines) == 5 and len(f.readlines()) > 5:
                    print("   ... (more lines)")
            except Exception as e:
                print(f"   Could not read script: {e}")

        # Check if config.yaml exists and show contents
        config_file = job_dir / "config.yaml"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    content = f.read()
                print("⚙️  Config:")
                for line in content.split("\n"):
                    if line.strip():
                        print(f"   {line}")
            except Exception as e:
                print(f"   Could not read config: {e}")

        print("-" * 50)

    def reset_all_jobs(self) -> None:
        """
        Delete all jobs and recreate the job folder structure.

        This will:
        1. Delete all jobs in inbox, approved, and done folders
        2. Recreate the empty folder structure
        3. Reset the known jobs tracking
        """
        root_email = self.config.email
        job_dir = self.config.get_job_dir(root_email)

        print(f"🔄 RESETTING ALL JOBS for {root_email}")
        print(f"📁 Target directory: {job_dir}")

        if not job_dir.exists():
            print("📭 No job directory found - nothing to reset")
            self._ensure_root_user_directories()
            return

        # Count jobs before deletion
        total_jobs = 0
        job_counts = {}

        for status_dir in ["inbox", "approved", "done"]:
            status_path = job_dir / status_dir
            if status_path.exists():
                job_list = [item for item in status_path.iterdir() if item.is_dir()]
                job_counts[status_dir] = len(job_list)
                total_jobs += len(job_list)

                if job_list:
                    print(f"📋 Found {len(job_list)} jobs in {status_dir}:")
                    for job in job_list[:5]:  # Show first 5
                        print(f"   - {job.name}")
                    if len(job_list) > 5:
                        print(f"   ... and {len(job_list) - 5} more")

        if total_jobs == 0:
            print("📭 No jobs found to delete")
            self._ensure_root_user_directories()
            return

        # Confirm deletion
        print(f"\n⚠️  WARNING: This will permanently delete {total_jobs} jobs!")
        print("   This action cannot be undone.")

        try:
            # Delete the entire job directory
            print(f"🗑️  Deleting job directory: {job_dir}")
            shutil.rmtree(job_dir)

            # Recreate the folder structure
            print("📁 Recreating job folder structure...")
            self._ensure_root_user_directories()

            # Reset known jobs tracking
            self.known_jobs.clear()

            print("✅ Job reset completed successfully!")
            print("📊 Summary:")
            print(f"   - Deleted {total_jobs} jobs total")
            for status, count in job_counts.items():
                if count > 0:
                    print(f"   - {status}: {count} jobs deleted")
            print("   - Clean folder structure recreated")

        except Exception as e:
            print(f"❌ Error during reset: {e}")
            print("🔧 Attempting to recreate folder structure anyway...")
            try:
                self._ensure_root_user_directories()
                print("✅ Folder structure recreated")
            except Exception as recovery_error:
                print(f"❌ Failed to recreate folders: {recovery_error}")
                raise

    def check_for_new_jobs(self) -> None:
        """Check for new jobs in the inbox and print them."""
        current_jobs = set(self._get_jobs_in_inbox())
        new_jobs = current_jobs - self.known_jobs

        for job_name in new_jobs:
            self._print_new_job(job_name)

        # Update known jobs
        self.known_jobs = current_jobs

    def run(self) -> None:
        """Start monitoring the inbox folder for new jobs."""
        root_email = self.config.email
        inbox_dir = self.config.get_inbox_dir(root_email)

        print("🚀 SyftJob Runner started")
        print(f"👤 Monitoring jobs for: {root_email}")
        print(f"📂 Inbox directory: {inbox_dir}")
        print(f"⏱️  Poll interval: {self.poll_interval} seconds")
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 50)

        # Initialize known jobs with current state
        self.known_jobs = set(self._get_jobs_in_inbox())
        if self.known_jobs:
            print(
                f"📋 Found {len(self.known_jobs)} existing jobs: {', '.join(self.known_jobs)}"
            )
        else:
            print("📭 No existing jobs found")
        print("-" * 50)

        try:
            while True:
                self.check_for_new_jobs()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n🛑 Job runner stopped by user")
        except Exception as e:
            print(f"\n❌ Job runner encountered an error: {e}")
            raise


def create_runner(syftbox_folder_path: str, poll_interval: int = 5) -> SyftJobRunner:
    """
    Factory function to create a SyftJobRunner from SyftBox folder.

    Args:
        syftbox_folder_path: Path to the SyftBox_{email} folder
        poll_interval: How often to check for new jobs (in seconds)

    Returns:
        Configured SyftJobRunner instance
    """
    config = SyftJobConfig.from_syftbox_folder(syftbox_folder_path)
    return SyftJobRunner(config, poll_interval)
