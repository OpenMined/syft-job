import re
from pathlib import Path

from pydantic import BaseModel, Field


class SyftJobConfig(BaseModel):
    """Configuration for SyftJob system."""

    syftbox_folder: str = Field(..., description="Path to SyftBox_{email} folder")
    email: str = Field(..., description="User email address extracted from folder name")
    server_url: str = Field(default="", description="Server URL (optional)")
    refresh_token: str = Field(
        default="", description="Authentication refresh token (optional)"
    )

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

    def get_inbox_dir(self, user_email: str) -> Path:
        """Get the inbox directory path for a specific user."""
        return self.get_job_dir(user_email) / "inbox"

    def get_approved_dir(self, user_email: str) -> Path:
        """Get the approved directory path for a specific user."""
        return self.get_job_dir(user_email) / "approved"

    def get_done_dir(self, user_email: str) -> Path:
        """Get the done directory path for a specific user."""
        return self.get_job_dir(user_email) / "done"
