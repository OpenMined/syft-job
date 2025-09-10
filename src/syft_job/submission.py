"""
Job submission interface for data scientists.

This module provides a simple interface for submitting jobs to the syft-job system.
Jobs are executed by generating a bash script (run.sh) that handles all setup and execution.

Job Structure Created:
    job-{uuid}/
    ├── config.yaml    # Job configuration with inputs/outputs
    ├── run.sh         # Generated bash script that runs the job  
    ├── inputs/        # Resolved input data files
    └── outputs/       # Job output files

Environment variables are created with the exact same names as the input keys:
- inputs={"TRAIN": "..."} → environment variable TRAIN
- inputs={"TEST": "..."} → environment variable TEST  
- inputs={"DATA": "..."} → environment variable DATA

Standard variables always available:
- CODE_DIR: Path to your code directory
- OUTPUT_DIR: Path to job outputs directory

Usage:
    import syft_job as sj
    
    result = sj.submit_job(
        name="my_analysis",
        code="./my_code",           # Your code directory
        inputs={
            "TRAIN": "syft://datasets/cancer_train.csv",
            "TEST": "./local/test.csv"
        },
        job_dir="./jobs"            # Where job workspaces are created
    )
    
    # In your code (my_code/main.py):
    # train_data = pd.read_csv(os.environ["TRAIN"])
    # test_data = pd.read_csv(os.environ["TEST"])
    # output_dir = os.environ["OUTPUT_DIR"]

The system generates a run.sh script that:
1. Sets up the environment (installs dependencies)
2. Exports all input variables  
3. Runs your code with the specified language
4. Handles all the complexity so you just write your analysis code
"""

import uuid
from typing import Dict, Optional, List, Any
from pathlib import Path

from .models import SimpleJobSubmission, JobSubmission, JobConfig, JobResult
from .runner import JobRunner


def submit_job(
    name: str,
    code: str,
    run_script: str,
    inputs: Optional[Dict[str, str]] = None,
    output_dir: Optional[str] = None,
    setup: Optional[str] = None,
    timeout: int = 300,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    sync: bool = True,
    job_dir: str = "./jobs",
    local_runner: Optional[JobRunner] = None
) -> JobResult:
    """
    Submit a job for execution in a local folder.
    
    This is the main interface for data scientists to submit jobs. Jobs are executed
    locally and job directories are created in the specified job_dir folder.
    
    Args:
        name: Job name
        code: Syft URL or path to code bundle (e.g., "syft://projects/user123/code" or "/path/to/code")
        run_script: Bash script content or path to script file that handles job execution
        inputs: Map of variable names to syft:// URLs or local paths for input data
        output_dir: Syft URL or local path for output directory
        setup: Setup script for environment configuration (e.g., "setup.sh")
        timeout: Timeout in seconds
        description: Job description
        tags: Job tags for organization
        metadata: Additional metadata
        sync: If True, wait for job completion; if False, return immediately
        job_dir: Base directory where job workspaces will be created (default: "./jobs")
        local_runner: Local JobRunner instance (if None, creates default)
    
    Returns:
        JobResult: The result of the job execution
    
    Examples:
        # Simple job submission with local folder
        result = submit_job(
            name="data_analysis",
            code="./my_code",
            inputs={
                "TRAIN": "syft://datasets/cancer_train.csv",
                "TEST": "./data/cancer_test.csv"
            },
            job_dir="./my_jobs"
        )
        
        # Python job with custom setup
        result = submit_job(
            name="ml_training",
            code="./ml_code", 
            inputs={"DATA": "./data/training_data.csv"},
            language="python",
            entrypoint="train.py",
            setup="setup.sh",
            job_dir="./experiments"
        )
        
        # Go job
        result = submit_job(
            name="data_processor",
            code="./go_processor",
            language="go",
            entrypoint="main.go",
            job_dir="./jobs"
        )
    """
    
    # Default values
    if inputs is None:
        inputs = {}
    if tags is None:
        tags = []
    if metadata is None:
        metadata = {}
    
    # Create the job submission
    simple_job = SimpleJobSubmission(
        name=name,
        code=code,
        inputs=inputs,
        output_dir=output_dir,
        setup=setup,
        run_script=run_script,
        timeout=timeout,
        description=description,
        tags=tags,
        metadata=metadata
    )
    
    # Convert to full JobSubmission format
    job_config = JobConfig(
        code=simple_job.code,
        setup=simple_job.setup,
        run_script=simple_job.run_script,
        inputs=simple_job.inputs,
        output_dir=simple_job.output_dir,
        timeout=simple_job.timeout
    )
    
    job_submission = JobSubmission(
        job_id=str(uuid.uuid4()),
        name=simple_job.name,
        description=simple_job.description,
        config=job_config,
        tags=simple_job.tags,
        metadata=simple_job.metadata
    )
    
    # Execute the job locally
    if local_runner is None:
        # Create runner with specified job directory
        local_runner = JobRunner(max_workers=1, job_dir=job_dir, cleanup=False)
    
    if sync:
        return local_runner.run_job(job_submission)
    else:
        import asyncio
        return asyncio.run(local_runner.run_job_async(job_submission))


def submit_batch_jobs(
    jobs: List[Dict[str, Any]],
    job_dir: str = "./jobs",
    local_runner: Optional[JobRunner] = None
) -> List[JobResult]:
    """
    Submit multiple jobs as a batch.
    
    Args:
        jobs: List of job specifications (same format as submit_job arguments)
        job_dir: Base directory where job workspaces will be created
        local_runner: Local JobRunner instance
    
    Returns:
        List[JobResult]: Results for all submitted jobs
    """
    job_submissions = []
    
    for job_spec in jobs:
        # Extract and validate job parameters
        name = job_spec.get("name", f"batch_job_{uuid.uuid4().hex[:8]}")
        code = job_spec["code"]
        
        # Require run_script for batch jobs too
        if "run_script" not in job_spec:
            raise ValueError(f"Job '{name}' must include 'run_script' parameter")
        
        simple_job = SimpleJobSubmission(
            name=name,
            code=code,
            inputs=job_spec.get("inputs", {}),
            output_dir=job_spec.get("output_dir"),
            setup=job_spec.get("setup"),
            run_script=job_spec["run_script"],
            timeout=job_spec.get("timeout", 300),
            description=job_spec.get("description"),
            tags=job_spec.get("tags", []),
            metadata=job_spec.get("metadata", {})
        )
        
        job_config = JobConfig(
            code=simple_job.code,
            setup=simple_job.setup,
            run_script=simple_job.run_script,
            inputs=simple_job.inputs,
            output_dir=simple_job.output_dir,
            timeout=simple_job.timeout
        )
        
        job_submission = JobSubmission(
            job_id=str(uuid.uuid4()),
            name=simple_job.name,
            description=simple_job.description,
            config=job_config,
            tags=simple_job.tags,
            metadata=simple_job.metadata
        )
        
        job_submissions.append(job_submission)
    
    # Execute batch locally
    if local_runner is None:
        local_runner = JobRunner(max_workers=4, job_dir=job_dir, cleanup=False)
    
    return local_runner.run_batch(job_submissions)


# Convenience aliases
submit = submit_job
submit_batch = submit_batch_jobs