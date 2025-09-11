import json
from pathlib import Path
from pydantic import BaseModel, Field


class SyftJobConfig(BaseModel):
    """Configuration for SyftJob system."""
    data_dir: str = Field(..., description="Root directory for SyftBox data")
    email: str = Field(..., description="User email address")
    server_url: str = Field(..., description="Server URL")
    refresh_token: str = Field(..., description="Authentication refresh token")

    @classmethod
    def from_file(cls, config_path: str) -> "SyftJobConfig":
        """Load configuration from JSON file."""
        config_path = Path(config_path).expanduser().resolve()
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return cls(**config_data)
    
    @property
    def datasites_dir(self) -> Path:
        """Get the datasites directory path."""
        return Path(self.data_dir) / "datasites"
    
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