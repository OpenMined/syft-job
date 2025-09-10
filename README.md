# Syft Job Submission System

A generic Python-based job submission and execution system that supports multiple programming languages and syft:// URL-based data references for secure, distributed data science workflows.

## Features

- **🚀 Easy Data Scientist Interface**: Simple `import syft_job as sj; sj.submit_job()` API
- **🔗 Syft URL Support**: Reference data using `syft://datasets/my-data.csv` URLs
- **🌍 Multi-language support**: Python, Go, Rust, Bash, Node.js, Java, Ruby, R, Julia, etc.
- **⚙️ Environment Variable Injection**: Input variables mapped directly (TRAIN, TEST, etc.)
- **🔧 Custom Setup Scripts**: Support for `setup.sh` to configure execution environment
- **📦 Batch processing**: Submit multiple jobs at once
- **🔄 Async and sync execution**: Submit jobs for immediate or background execution
- **📊 Job management**: Track status, cancel jobs, retrieve results
- **🎯 Resource management**: Configurable timeouts, environment variables, working directories
- **🌐 RESTful API**: Easy integration with any client (legacy compatibility)

## Installation

```bash
# Install dependencies
uv sync

# Or with pip
pip install -e .
```

## Quick Start

### 🚀 New Syft Interface (Recommended)

The easiest way for data scientists to submit jobs:

```python
import syft_job as sj

# Submit a simple Python job
result = sj.submit_job(
    name="Data Analysis", 
    code="syft://projects/user123/analysis-code",
    inputs={
        "TRAIN": "syft://datasets/cancer_train.csv",
        "TEST": "syft://datasets/cancer_test.csv"
    },
    output_dir="syft://results/user123/job-output"
)

print(f"Job completed with status: {result.status}")
print(result.output)
```

### Data Scientist Code Example

Your job code automatically gets environment variables:

```python
# train.py
import os
import pandas as pd

# Environment variables are automatically set by the runner
train_data = pd.read_csv(os.environ["TRAIN"])    # Points to resolved file
test_data = pd.read_csv(os.environ["TEST"])      # Points to resolved file
output_dir = os.environ["OUTPUT_DIR"]            # Output directory path

# Your ML code here...
model = train_model(train_data, test_data)

# Save results
model.save(f"{output_dir}/model.pkl")
```

### Multi-Language Support

**Go Example:**
```python
result = sj.submit_job(
    name="Go Data Processor",
    code="syft://projects/user123/go-processor", 
    inputs={"DATA": "syft://datasets/large_dataset.csv"},
    language="go",
    entrypoint="main.go"
)
```

**With Custom Setup:**
```python
result = sj.submit_job(
    name="ML Training Job",
    code="syft://projects/user123/ml-training",
    inputs={"DATA": "syft://datasets/training_data.csv"}, 
    setup="setup.sh",  # Custom environment setup
    language="python"
)
```

### 📁 Folder-Based Job Execution

Jobs are executed locally and create workspaces in the specified directory:

```python
# Jobs will be created in ./my_jobs/ directory
result = sj.submit_job(
    name="Analysis",
    code="./my_code_folder", 
    inputs={"DATA": "./data/input.csv"},
    job_dir="./my_jobs"  # Job workspaces created here
)

# Check job workspace at: ./my_jobs/{job_id}/
```

## Folder Structure

After running jobs, your directory structure will look like:

```
my_project/
├── my_code/           # Your source code
├── data/              # Your input data  
└── my_jobs/           # Job workspaces (one per job)
    ├── job-abc123/    # Individual job workspace
    │   ├── code/      # Copied/extracted job code
    │   ├── inputs/    # Resolved input data files
    │   └── outputs/   # Job output files
    └── job-def456/
        ├── code/
        ├── inputs/ 
        └── outputs/
```

## Usage Examples

### Simple Python Job

```python
import syft_job as sj

result = sj.submit_job(
    name="Data Analysis",
    code="./analysis_code",  # Local folder with your Python code
    inputs={
        "TRAIN": "./data/train.csv",  # Local file
        "TEST": "syft://datasets/test.csv"  # Syft URL (resolved automatically)
    },
    job_dir="./jobs"  # Where to create job workspaces
)
```

### Multi-Language Support

```python
# Python job
result = sj.submit_job(name="python_job", code="./py_code", language="python")

# Go job  
result = sj.submit_job(name="go_job", code="./go_code", language="go", entrypoint="main.go")

# With custom setup
result = sj.submit_job(name="custom_job", code="./code", setup="setup.sh")
```

### Batch Processing

```python
jobs = [
    {"name": f"Job {i}", "code": "./worker_code", "inputs": {"DATA": f"./data_{i}.csv"}}
    for i in range(10)
]

results = sj.submit_batch_jobs(jobs, job_dir="./batch_jobs")
```

## Running Examples

```bash
# Run the folder-based examples
python example_usage.py

# Or use the CLI
syft-job --example --job-dir ./my_jobs
```

## Development

```bash
# Install in development mode
uv sync

# Run examples
syft-job --example

# Run tests (if available)
pytest
```

## Job Workspace Inspection

Job workspaces are preserved by default for inspection:

```bash
# List job workspaces
ls ./jobs/

# Inspect a specific job
ls ./jobs/job-abc123/
  code/      # Your code that was executed
  inputs/    # Input data files that were provided
  outputs/   # Files created by your job
```
