from .models import JobSubmission, JobResult, JobStatus, JobConfig, SimpleJobSubmission
from .runner import JobRunner
from .submission import submit_job, submit_batch_jobs, submit, submit_batch

__all__ = [
    # Models
    "JobSubmission", "JobResult", "JobStatus", "JobConfig", "SimpleJobSubmission",
    # Core components
    "JobRunner",
    # Main submission interface
    "submit_job", "submit_batch_jobs",
    # Convenience aliases
    "submit", "submit_batch"
]


def main() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(description="Syft Job Submission System")
    parser.add_argument("--example", action="store_true", help="Run example job submissions")
    parser.add_argument("--job-dir", default="./jobs", help="Directory to create job workspaces in")
    parser.add_argument("--cleanup", action="store_true", help="Clean up job workspaces after completion")
    
    args = parser.parse_args()
    
    if args.example:
        print("Running example job submissions...")
        from .example import run_examples
        run_examples(job_dir=args.job_dir, cleanup=args.cleanup)
    else:
        print("Syft Job Submission System")
        print("Usage:")
        print("  import syft_job as sj")
        print("  result = sj.submit_job(...)")
        print("")
        print("For examples, run: syft-job --example")
