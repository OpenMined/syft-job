import asyncio
import subprocess
import os
import uuid
import json
import tempfile
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging
from urllib.parse import urlparse

from .models import JobSubmission, JobResult, JobStatus, JobConfig


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobRunner:
    def __init__(self, 
                 max_workers: int = 4,
                 job_dir: Optional[str] = None,
                 cleanup: bool = True):
        self.max_workers = max_workers
        # Default to "./jobs" instead of temp directory for better control
        self.job_dir = Path(job_dir) if job_dir else Path("./jobs")
        self.cleanup = cleanup
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs: Dict[str, JobResult] = {}
        self._running_processes: Dict[str, subprocess.Popen] = {}
        
        logger.info(f"JobRunner initialized with job directory: {self.job_dir.absolute()}")
    
    def resolve_syft_url(self, syft_url: str, target_dir: Path) -> Path:
        """
        Resolve a syft:// URL to a local file path.
        
        This is a mock implementation. In a real system, this would:
        1. Connect to the Syft registry/index service
        2. Resolve the URL to an actual storage location (S3, MinIO, etc.)
        3. Download/decrypt/mount the file
        4. Return the local path
        
        For now, we'll create stub files for demonstration.
        """
        if not syft_url.startswith("syft://"):
            # If it's not a syft URL, treat as local path
            return Path(syft_url)
        
        # Mock resolution: convert syft://path/to/resource to local path
        resource_path = syft_url.replace("syft://", "").replace("/", "_")
        local_path = target_dir / resource_path
        
        logger.info(f"Resolving syft URL {syft_url} to {local_path}")
        
        # Create stub file/directory
        if not local_path.exists():
            if resource_path.endswith((".tar.gz", ".zip", ".tar")):
                # Create empty archive for code bundles
                local_path.write_text("# Stub code file\nprint('Hello from syft job!')\n")
            else:
                # Create stub data file
                local_path.write_text(f"# Stub data from {syft_url}\ndata,value\n1,test\n2,data\n")
        
        return local_path
    
    def _extract_code_bundle(self, archive_path: Path, extract_to: Path) -> None:
        """Extract code bundle from archive."""
        extract_to.mkdir(parents=True, exist_ok=True)
        
        if archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.suffix in ['.tar', '.tar.gz', '.tgz']:
            with tarfile.open(archive_path, 'r') as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            # If it's not an archive, copy as single file
            shutil.copy2(archive_path, extract_to / archive_path.name)
    
    
    def _prepare_job_environment(self, job: JobSubmission) -> Dict[str, Path]:
        """
        Prepare the job execution environment with config.yaml and run.sh structure.
        
        Creates:
            job-{id}/
            ├── config.yaml    # Job configuration
            └── run.sh         # Bash script that runs the job
        
        Returns:
            Dict with paths: {
                'workspace': job_workspace,
                'config_file': config_yaml_path,
                'run_script': run_sh_path
            }
        """
        job_workspace = self.job_dir / job.job_id
        job_workspace.mkdir(parents=True, exist_ok=True)
        
        # Resolve code directory (where the actual code lives)
        code_dir = None
        if job.config.code:
            logger.info(f"Resolving code location: {job.config.code}")
            code_dir = self.resolve_syft_url(job.config.code, job_workspace.parent)
            if not code_dir.exists():
                raise RuntimeError(f"Code directory not found: {code_dir}")
        
        # Create inputs directory and resolve input files
        inputs_dir = job_workspace / "inputs"
        inputs_dir.mkdir(exist_ok=True)
        
        input_env_vars = {}
        if job.config.inputs:
            for var_name, syft_url in job.config.inputs.items():
                logger.info(f"Resolving input {var_name}: {syft_url}")
                input_file = self.resolve_syft_url(syft_url, inputs_dir)
                input_env_vars[var_name.upper()] = str(input_file)
        
        # Create outputs directory
        outputs_dir = job_workspace / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        # Prepare environment variables for the job
        job_env_vars = {
            "CODE_DIR": str(code_dir) if code_dir else "",
            "OUTPUT_DIR": str(outputs_dir),
            **input_env_vars
        }
        
        # Create config.yaml
        config_yaml = job_workspace / "config.yaml"
        import yaml
        config_data = {
            "job": {
                "name": job.name,
                "code": str(code_dir) if code_dir else "",
                "inputs": dict(job.config.inputs) if job.config.inputs else {},
                "output_dir": str(outputs_dir),
                "environment": job_env_vars
            }
        }
        
        with open(config_yaml, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        # Create run.sh script
        run_sh = job_workspace / "run.sh"
        run_script_content = self._generate_run_script(job, job_env_vars)
        run_sh.write_text(run_script_content)
        run_sh.chmod(0o755)
        
        # Store environment variables in job config for runner execution
        job.config.env_vars.update(job_env_vars)
        
        logger.info(f"Job environment prepared at: {job_workspace}")
        logger.info(f"Code directory: {code_dir}")
        logger.info(f"Environment variables: {list(job_env_vars.keys())}")
        
        return {
            'workspace': job_workspace,
            'config_file': config_yaml,
            'run_script': run_sh
        }
    
    def _process_custom_run_script(self, run_script: str, job: JobSubmission, env_vars: Dict[str, str]) -> str:
        """Process custom run script - either inline content or file path."""
        from pathlib import Path
        
        # Check if run_script is a file path or inline content
        script_content = None
        
        if run_script.startswith(("#!/bin/bash", "#!", "echo ", "python ", "go ", "cd ")) or "\n" in run_script:
            # Likely inline script content
            script_content = run_script
        else:
            # Likely a file path
            script_path = Path(run_script)
            if not script_path.is_absolute():
                # For relative paths, first try the script as is
                if not script_path.exists():
                    # If relative to code directory, try that
                    if job.config.code:
                        code_path = Path(job.config.code)
                        if code_path.exists() and code_path.is_dir():
                            # Extract just the filename and look in code directory
                            script_name = Path(run_script).name
                            potential_script = code_path / script_name
                            if potential_script.exists():
                                script_path = potential_script
            
            if script_path.exists():
                script_content = script_path.read_text()
                logger.info(f"Loaded custom run script from: {script_path}")
            else:
                logger.warning(f"Custom run script file not found: {script_path}")
                # Fall back to treating it as inline content
                script_content = run_script
        
        # Ensure the script has a proper shebang
        if not script_content.startswith("#!"):
            script_content = "#!/bin/bash\nset -e\n\n" + script_content
        
        # Add environment variable info at the beginning (after shebang)
        lines = script_content.split('\n')
        enhanced_lines = []
        
        # Keep shebang and initial settings
        i = 0
        while i < len(lines) and (lines[i].startswith("#!") or lines[i].strip() in ["", "set -e", "set -x"]):
            enhanced_lines.append(lines[i])
            i += 1
        
        # Add job info
        enhanced_lines.extend([
            "",
            f"echo \"[JOB] Starting custom job: {job.name}\"",
            "echo \"[JOB] Working directory: $(pwd)\"", 
            "echo \"[JOB] Code directory: $CODE_DIR\"",
            "echo \"[JOB] Output directory: $OUTPUT_DIR\"",
            "echo \"[JOB] Environment variables:\"",
            "env | grep -E \"(CODE_DIR|OUTPUT_DIR|TRAIN|TEST|DATA|CONFIG)\" | sort",
            ""
        ])
        
        # Add the rest of the custom script
        enhanced_lines.extend(lines[i:])
        
        return '\n'.join(enhanced_lines)
    
    def _generate_run_script(self, job: JobSubmission, env_vars: Dict[str, str]) -> str:
        """Process the user-provided bash script."""
        
        # Always use the provided run_script (it's now required)
        return self._process_custom_run_script(job.config.run_script, job, env_vars)
    

    def _run_job_sync(self, job: JobSubmission) -> JobResult:
        start_time = datetime.now()
        result = JobResult(
            job_id=job.job_id,
            status=JobStatus.RUNNING,
            start_time=start_time,
            metadata=job.metadata
        )
        
        try:
            # Prepare environment - creates config.yaml and run.sh
            paths = self._prepare_job_environment(job)
            workspace = paths['workspace']
            run_script = paths['run_script']
            outputs_dir = workspace / "outputs"
            
            # Setup environment variables for the bash script
            env = os.environ.copy()
            env.update(job.config.env_vars)
            
            # Execute the run.sh script - this is all we need to do!
            command = ["bash", str(run_script)]
            
            logger.info(f"Executing job {job.job_id}: {' '.join(command)}")
            logger.info(f"Working directory: {workspace}")
            logger.info(f"Environment variables: {list(job.config.env_vars.keys())}")
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(workspace),
                env=env,
                text=True
            )
            
            self._running_processes[job.job_id] = process
            
            try:
                stdout, stderr = process.communicate(timeout=job.config.timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                result.status = JobStatus.FAILED
                result.error = f"Job timed out after {job.config.timeout} seconds"
                exit_code = -1
            finally:
                if job.job_id in self._running_processes:
                    del self._running_processes[job.job_id]
            
            # Collect artifacts from output directory
            artifacts = []
            if outputs_dir.exists():
                artifacts = [str(f) for f in outputs_dir.rglob("*") if f.is_file()]
            
            result.output = stdout
            result.error = stderr if stderr else None
            result.exit_code = exit_code
            result.status = JobStatus.COMPLETED if exit_code == 0 else JobStatus.FAILED
            result.artifacts = artifacts
            
        except Exception as e:
            logger.error(f"Job {job.job_id} failed with error: {str(e)}")
            result.status = JobStatus.FAILED
            result.error = str(e)
            result.exit_code = -1
        finally:
            result.end_time = datetime.now()
            result.duration = (result.end_time - start_time).total_seconds()
            
            if self.cleanup and job.job_id:
                workspace_path = self.job_dir / job.job_id
                if workspace_path.exists():
                    logger.info(f"Cleaning up job workspace: {workspace_path}")
                    shutil.rmtree(workspace_path)
            else:
                workspace_path = self.job_dir / job.job_id
                logger.info(f"Job workspace preserved at: {workspace_path.absolute()}")
        
        self.jobs[job.job_id] = result
        return result
    
    async def run_job_async(self, job: JobSubmission) -> JobResult:
        if not job.job_id:
            job.job_id = str(uuid.uuid4())
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self._run_job_sync,
            job
        )
        return result
    
    def run_job(self, job: JobSubmission) -> JobResult:
        if not job.job_id:
            job.job_id = str(uuid.uuid4())
        
        return self._run_job_sync(job)
    
    async def run_batch_async(self, jobs: List[JobSubmission]) -> List[JobResult]:
        tasks = [self.run_job_async(job) for job in jobs]
        results = await asyncio.gather(*tasks)
        return results
    
    def run_batch(self, jobs: List[JobSubmission]) -> List[JobResult]:
        return asyncio.run(self.run_batch_async(jobs))
    
    def cancel_job(self, job_id: str) -> bool:
        if job_id in self._running_processes:
            process = self._running_processes[job_id]
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            if job_id in self.jobs:
                self.jobs[job_id].status = JobStatus.CANCELLED
            return True
        return False
    
    def get_job_status(self, job_id: str) -> Optional[JobResult]:
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> Dict[str, JobResult]:
        return self.jobs.copy()
    
    def cleanup_workspace(self):
        if self.job_dir.exists():
            shutil.rmtree(self.job_dir)
            self.job_dir.mkdir(parents=True, exist_ok=True)
    
    def __del__(self):
        self.executor.shutdown(wait=False)
        for process in self._running_processes.values():
            try:
                process.terminate()
            except:
                pass