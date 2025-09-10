from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Union
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobConfig(BaseModel):
    # Code configuration
    code: Optional[str] = Field(None, description="Syft URL or path to code bundle")
    setup: Optional[str] = Field(None, description="Setup script (e.g., setup.sh) for custom environment configuration")
    run_script: str = Field(..., description="Bash script content or path to script file that handles job execution")
    
    # Input/Output configuration with syft:// URLs
    inputs: Dict[str, str] = Field(default_factory=dict, description="Map of variable names to syft:// URLs for input data")
    output_dir: Optional[str] = Field(None, description="Syft URL for output directory")
    outputs: Dict[str, str] = Field(default_factory=dict, description="Map of variable names to syft:// URLs for output files")
    
    # Environment and execution
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    working_dir: Optional[str] = Field(None, description="Working directory for job execution")
    timeout: Optional[int] = Field(300, description="Timeout in seconds")
    resources: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Resource requirements")
    
    # Legacy support
    legacy_inputs: List[str] = Field(default_factory=list, description="Legacy: List of input files", alias="inputs_legacy")
    legacy_entrypoint: Optional[str] = Field(None, description="Legacy: Direct file path to execute", alias="entrypoint_legacy")


class JobSubmission(BaseModel):
    job_id: Optional[str] = Field(None, description="Unique job identifier")
    name: str = Field(..., description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    config: JobConfig = Field(..., description="Job configuration")
    tags: List[str] = Field(default_factory=list, description="Job tags for organization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class JobResult(BaseModel):
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Job execution status")
    output: Optional[str] = Field(None, description="Job output/stdout")
    error: Optional[str] = Field(None, description="Job error/stderr")
    exit_code: Optional[int] = Field(None, description="Process exit code")
    start_time: Optional[datetime] = Field(None, description="Job start time")
    end_time: Optional[datetime] = Field(None, description="Job end time")
    duration: Optional[float] = Field(None, description="Execution duration in seconds")
    artifacts: List[str] = Field(default_factory=list, description="Output file paths")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional result metadata")


class SimpleJobSubmission(BaseModel):
    """Simplified job submission model for data scientists"""
    name: str = Field(..., description="Job name")
    code: str = Field(..., description="Syft URL or path to code bundle")
    run_script: str = Field(..., description="Bash script content or path to script file that handles job execution")
    inputs: Dict[str, str] = Field(default_factory=dict, description="Map of variable names to syft:// URLs")
    output_dir: Optional[str] = Field(None, description="Syft URL for output directory")
    setup: Optional[str] = Field(None, description="Setup script for environment configuration")
    timeout: int = Field(300, description="Timeout in seconds")
    description: Optional[str] = Field(None, description="Job description")
    tags: List[str] = Field(default_factory=list, description="Job tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")