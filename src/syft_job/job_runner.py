import time
import os
from pathlib import Path
from typing import Set, List
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
                with open(run_script, 'r') as f:
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
                with open(config_file, 'r') as f:
                    content = f.read()
                print("⚙️  Config:")
                for line in content.split('\n'):
                    if line.strip():
                        print(f"   {line}")
            except Exception as e:
                print(f"   Could not read config: {e}")
        
        print("-" * 50)
    
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
        
        print(f"🚀 SyftJob Runner started")
        print(f"👤 Monitoring jobs for: {root_email}")
        print(f"📂 Inbox directory: {inbox_dir}")
        print(f"⏱️  Poll interval: {self.poll_interval} seconds")
        print(f"⏹️  Press Ctrl+C to stop")
        print("=" * 50)
        
        # Initialize known jobs with current state
        self.known_jobs = set(self._get_jobs_in_inbox())
        if self.known_jobs:
            print(f"📋 Found {len(self.known_jobs)} existing jobs: {', '.join(self.known_jobs)}")
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


def create_runner(config_path: str, poll_interval: int = 5) -> SyftJobRunner:
    """
    Factory function to create a SyftJobRunner from config file.
    
    Args:
        config_path: Path to the configuration JSON file
        poll_interval: How often to check for new jobs (in seconds)
        
    Returns:
        Configured SyftJobRunner instance
    """
    config = SyftJobConfig.from_file(config_path)
    return SyftJobRunner(config, poll_interval)