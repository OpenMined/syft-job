import re
from pathlib import Path

from pydantic import BaseModel, Field


class SyftJobConfig(BaseModel):
    """Configuration for SyftJob system."""

    syftbox_folder: str = Field(..., description="Path to SyftBox_{email} folder")
    email: str = Field(..., description="User email address extracted from folder name")

    @classmethod
    def from_syftbox_folder(cls, syftbox_folder_path: str) -> "SyftJobConfig":
        """Load configuration from SyftBox folder path."""
        syftbox_path = Path(syftbox_folder_path).expanduser().resolve()

        if not syftbox_path.exists():
            raise FileNotFoundError(f"SyftBox folder not found: {syftbox_folder_path}")

        if not syftbox_path.is_dir():
            raise ValueError(f"Path is not a directory: {syftbox_folder_path}")

        # Extract email from folder name (SyftBox_{email})
        folder_name = syftbox_path.name
        match = re.match(r"^SyftBox_(.+)$", folder_name)
        if not match:
            raise ValueError(
                f"Invalid SyftBox folder name format. Expected 'SyftBox_{{email}}', got: {folder_name}"
            )

        email = match.group(1)

        return cls(syftbox_folder=str(syftbox_path), email=email)

    @classmethod
    def from_file(cls, config_path: str) -> "SyftJobConfig":
        """Deprecated: Load configuration from JSON file. Use from_syftbox_folder instead."""
        raise DeprecationWarning(
            "from_file is deprecated. Use from_syftbox_folder instead."
        )

    @property
    def datasites_dir(self) -> Path:
        """Get the datasites directory path."""
        return Path(self.syftbox_folder) / "datasites"

    def get_user_dir(self, user_email: str) -> Path:
        """Get the directory path for a specific user."""
        return self.datasites_dir / user_email

    def get_job_dir(self, user_email: str) -> Path:
        """Get the job directory path for a specific user."""
        return self.get_user_dir(user_email) / "app_data" / "job"

    def get_job_status(self, job_path: Path) -> str:
        """
        Get the status of a job based on marker files.

        Args:
            job_path: Path to the job directory

        Returns:
            str: Status of the job ('inbox', 'approved', or 'done')
        """
        if not job_path.is_dir():
            raise ValueError(f"Job path is not a directory: {job_path}")

        # Check for status files in priority order
        if (job_path / "done").exists():
            return "done"
        elif (job_path / "approved").exists():
            return "approved"
        else:
            return "inbox"

    def create_approved_marker(self, job_path: Path) -> None:
        """
        Create approved marker file in job directory.

        Args:
            job_path: Path to the job directory
        """
        marker_file = job_path / "approved"
        marker_file.touch()

    def create_done_marker(self, job_path: Path) -> None:
        """
        Create done marker file in job directory.

        Args:
            job_path: Path to the job directory
        """
        marker_file = job_path / "done"
        marker_file.touch()

    def is_job_approved(self, job_path: Path) -> bool:
        """Check if job has been approved (has approved file)."""
        return (job_path / "approved").exists()

    def is_job_done(self, job_path: Path) -> bool:
        """Check if job has been completed (has done file)."""
        return (job_path / "done").exists()

    def is_job_inbox(self, job_path: Path) -> bool:
        """Check if job is still in inbox (no status markers)."""
        return not self.is_job_approved(job_path) and not self.is_job_done(job_path)
