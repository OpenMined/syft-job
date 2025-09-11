from .client import JobClient, get_client
from .config import SyftJobConfig
from .job_runner import SyftJobRunner, create_runner

__all__ = [
    # Models
    "JobSubmission",
    "JobResult",
    "JobStatus",
    "JobConfig",
    "SimpleJobSubmission",
    # Core components
    "JobRunner",
    # Main submission interface
    "submit_job",
    "submit_batch_jobs",
    # Convenience aliases
    "submit",
    "submit_batch",
    # New SyftBox job system
    "JobClient",
    "get_client",
    "SyftJobConfig",
    "SyftJobRunner",
    "create_runner",
]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Syft Job Submission System")
    parser.add_argument(
        "--job-dir", default="./jobs", help="Directory to create job workspaces in"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up job workspaces after completion",
    )

    parser.parse_args()

    print("Syft Job Submission System")
    print("Usage:")
    print("  import syft_job as sj")
    print("  result = sj.submit_job(...)")
