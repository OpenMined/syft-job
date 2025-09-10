#!/usr/bin/env python3

"""
Example usage of the Syft Job Submission System.

This demonstrates how to submit jobs that will be executed in local folders,
with syft:// URL support and environment variable injection.
"""

import os
import json
import time
from pathlib import Path
import shutil

# Import syft-job for the new interface
import syft_job as sj


def create_sample_data():
    """Create sample data files for testing."""
    data_dir = Path("./sample_data")
    data_dir.mkdir(exist_ok=True)
    
    # Create train data
    train_data = data_dir / "train.csv" 
    train_data.write_text("id,feature1,feature2,label\n1,0.1,0.2,A\n2,0.3,0.4,B\n3,0.5,0.6,A\n")
    
    # Create test data
    test_data = data_dir / "test.csv"
    test_data.write_text("id,feature1,feature2\n4,0.7,0.8\n5,0.9,1.0\n")
    
    return str(data_dir)


def create_python_job():
    """Create a simple Python job."""
    job_dir = Path("./sample_jobs/python_job")
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the main Python script
    main_py = job_dir / "main.py"
    main_py.write_text("""
import os
import pandas as pd
import json

print("[JOB] Starting Python data analysis job...")
print(f"[JOB] Working directory: {os.getcwd()}")

# Read environment variables for inputs (automatically set by runner)
train_file = os.environ.get("TRAIN", "No TRAIN data")
test_file = os.environ.get("TEST", "No TEST data")
output_dir = os.environ.get("OUTPUT_DIR", "./outputs")

print(f"[JOB] Train data: {train_file}")
print(f"[JOB] Test data: {test_file}")
print(f"[JOB] Output directory: {output_dir}")

# Read and process data
if os.path.exists(train_file):
    train_data = pd.read_csv(train_file)
    print(f"[JOB] Loaded training data: {len(train_data)} rows")
    print(train_data.head())

if os.path.exists(test_file):
    test_data = pd.read_csv(test_file)
    print(f"[JOB] Loaded test data: {len(test_data)} rows")

# Create some results
results = {
    "job_type": "python_analysis",
    "status": "completed",
    "train_rows": len(train_data) if os.path.exists(train_file) else 0,
    "test_rows": len(test_data) if os.path.exists(test_file) else 0,
    "timestamp": pd.Timestamp.now().isoformat()
}

# Write results
os.makedirs(output_dir, exist_ok=True)
with open(os.path.join(output_dir, "analysis_results.json"), "w") as f:
    json.dump(results, f, indent=2)

print("[JOB] Analysis complete! Results saved.")
""")
    
    # Create requirements.txt
    requirements = job_dir / "requirements.txt"
    requirements.write_text("pandas>=1.0.0\\n")
    
    return str(job_dir)


def create_go_job():
    """Create a simple Go job."""
    job_dir = Path("./sample_jobs/go_job")
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Create main.go
    main_go = job_dir / "main.go"
    main_go.write_text("""
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

type Result struct {
	JobType   string    `json:"job_type"`
	Status    string    `json:"status"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
}

func main() {
	fmt.Println("[GO JOB] Starting Go data processor...")
	
	// Read environment variables
	trainFile := os.Getenv("TRAIN")
	testFile := os.Getenv("TEST")
	outputDir := os.Getenv("OUTPUT_DIR")
	
	fmt.Printf("[GO JOB] Train file: %s\\n", trainFile)
	fmt.Printf("[GO JOB] Test file: %s\\n", testFile)
	fmt.Printf("[GO JOB] Output dir: %s\\n", outputDir)
	
	// Create output directory
	os.MkdirAll(outputDir, 0755)
	
	// Process data (simplified)
	result := Result{
		JobType:   "go_processor",
		Status:    "completed",
		Message:   "Data processing completed successfully",
		Timestamp: time.Now(),
	}
	
	// Write result
	resultFile := filepath.Join(outputDir, "processing_results.json")
	file, err := os.Create(resultFile)
	if err != nil {
		fmt.Printf("Error creating result file: %v\\n", err)
		return
	}
	defer file.Close()
	
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(result); err != nil {
		fmt.Printf("Error writing result: %v\\n", err)
		return
	}
	
	fmt.Println("[GO JOB] Processing complete! Results saved.")
}
""")
    
    # Create go.mod
    go_mod = job_dir / "go.mod"
    go_mod.write_text("module sample_job\\n\\ngo 1.21\\n")
    
    return str(job_dir)


def create_job_with_setup():
    """Create a job with custom setup script."""
    job_dir = Path("./sample_jobs/setup_job")
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Create setup script
    setup_sh = job_dir / "setup.sh"
    setup_sh.write_text("""#!/bin/bash
set -e

echo "[SETUP] Configuring job environment..."
echo "[SETUP] Current directory: $(pwd)"
echo "[SETUP] Available environment variables:"
env | grep -E "(TRAIN|TEST|OUTPUT_DIR|CODE_DIR|INPUT_DIR)" | sort

# Install Python dependencies if they exist
if [ -f "requirements.txt" ]; then
    echo "[SETUP] Installing Python dependencies..."
    pip install -r requirements.txt
fi

echo "[SETUP] Environment setup complete!"
""")
    setup_sh.chmod(0o755)
    
    # Create main script
    main_py = job_dir / "main.py"
    main_py.write_text("""
import os
import json

print("[JOB] Job with custom setup running...")

# Check environment
env_vars = {k: v for k, v in os.environ.items() if k in ["TRAIN", "TEST", "CONFIG", "OUTPUT_DIR", "CODE_DIR", "INPUT_DIR"]}
print("[JOB] Job environment variables:")
for k, v in env_vars.items():
    print(f"  {k} = {v}")

# Create output
output_dir = os.environ.get("OUTPUT_DIR", "./outputs")
os.makedirs(output_dir, exist_ok=True)

result = {
    "message": "Job with custom setup completed",
    "environment_variables": env_vars,
    "setup_worked": True
}

with open(os.path.join(output_dir, "setup_job_results.json"), "w") as f:
    json.dump(result, f, indent=2)

print("[JOB] Setup job completed successfully!")
""")
    
    return str(job_dir)


def example_python_job():
    """Submit a Python job with syft:// URLs and local paths."""
    print("\\n=== Python Job Submission ===")
    
    data_dir = create_sample_data()
    python_job_dir = create_python_job()
    
    # Python execution script
    python_script = """#!/bin/bash
set -e

echo "[JOB] Installing Python dependencies..."
if [ -f "$CODE_DIR/requirements.txt" ]; then
    pip install -r "$CODE_DIR/requirements.txt"
fi

echo "[JOB] Running Python analysis..."
python "$CODE_DIR/main.py"

echo "[JOB] Python job completed!"
"""
    
    result = sj.submit_job(
        name="Python Data Analysis",
        code=python_job_dir,
        run_script=python_script,
        inputs={
            "TRAIN": f"{data_dir}/train.csv",  # Local path
            "TEST": "syft://datasets/test_data.csv"  # Syft URL (will be mocked)
        },
        output_dir="syft://results/python_analysis",
        job_dir="./jobs",
        sync=True
    )
    
    print(f"Job ID: {result.job_id}")
    print(f"Status: {result.status}")
    print(f"Duration: {result.duration:.2f}s")
    if result.output:
        print(f"Output:\\n{result.output}")
    if result.artifacts:
        print(f"Artifacts created: {len(result.artifacts)} files")
        for artifact in result.artifacts:
            print(f"  - {artifact}")
    
    return result.job_id


def example_go_job():
    """Submit a Go job."""
    print("\\n=== Go Job Submission ===")
    
    go_job_dir = create_go_job()
    
    # Go execution script
    go_script = """#!/bin/bash
set -e

echo "[JOB] Building Go program..."
cd "$CODE_DIR"
go build -o "$OUTPUT_DIR/job_binary" main.go

echo "[JOB] Running Go program..."
"$OUTPUT_DIR/job_binary"

echo "[JOB] Go job completed!"
"""
    
    result = sj.submit_job(
        name="Go Data Processor", 
        code=go_job_dir,
        run_script=go_script,
        inputs={
            "TRAIN": "syft://datasets/large_data.csv",
            "TEST": "syft://datasets/validation_data.csv"
        },
        job_dir="./jobs",
        timeout=60,
        sync=True
    )
    
    print(f"Go Job ID: {result.job_id}")
    print(f"Status: {result.status}")
    print(f"Duration: {result.duration:.2f}s")
    if result.output:
        print(f"Output:\\n{result.output}")
    if result.artifacts:
        print(f"Artifacts: {result.artifacts}")
    
    return result.job_id


def example_job_with_setup():
    """Submit a job with custom setup script."""
    print("\\n=== Job with Custom Setup ===")
    
    job_dir = create_job_with_setup()
    
    # Python with setup script
    setup_script = """#!/bin/bash
set -e

echo "[JOB] Running custom setup..."
if [ -f "$CODE_DIR/setup.sh" ]; then
    bash "$CODE_DIR/setup.sh"
fi

echo "[JOB] Running Python script..."
python "$CODE_DIR/main.py"

echo "[JOB] Setup job completed!"
"""
    
    result = sj.submit_job(
        name="Job with Custom Setup",
        code=job_dir,
        run_script=setup_script,
        inputs={
            "CONFIG": "syft://configs/job_config.json"
        },
        job_dir="./jobs",
        sync=True
    )
    
    print(f"Setup Job ID: {result.job_id}")
    print(f"Status: {result.status}")
    print(f"Duration: {result.duration:.2f}s")
    if result.output:
        print(f"Output:\\n{result.output}")
    
    return result.job_id


def create_custom_bash_script_job():
    """Create a job that uses a custom bash script."""
    job_dir = Path("./sample_jobs/custom_bash_job")
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a custom bash script
    custom_script = job_dir / "custom_run.sh"
    custom_script.write_text("""#!/bin/bash
set -e

echo "[CUSTOM] This is a custom bash script execution!"
echo "[CUSTOM] Code directory: $CODE_DIR"
echo "[CUSTOM] Output directory: $OUTPUT_DIR"

# Check if we have training data
if [ -n "$TRAIN" ]; then
    echo "[CUSTOM] Processing training data: $TRAIN"
    wc -l "$TRAIN" || echo "Could not count lines in $TRAIN"
fi

# Create some custom output
echo "[CUSTOM] Creating custom analysis results..."
cat > "$OUTPUT_DIR/custom_analysis.txt" << 'EOF'
Custom Analysis Results
======================
Script: custom_run.sh
Environment: bash
Status: completed successfully
Timestamp: $(date)
EOF

# Create a JSON result
python3 -c "
import json
import os
from datetime import datetime

result = {
    'analysis_type': 'custom_bash_script',
    'status': 'completed',
    'timestamp': datetime.now().isoformat(),
    'environment_vars': {
        'CODE_DIR': os.environ.get('CODE_DIR', 'not_set'),
        'OUTPUT_DIR': os.environ.get('OUTPUT_DIR', 'not_set'),
        'TRAIN': os.environ.get('TRAIN', 'not_set')
    }
}

with open(os.path.join(os.environ['OUTPUT_DIR'], 'custom_results.json'), 'w') as f:
    json.dump(result, f, indent=2)
"

echo "[CUSTOM] Custom script completed successfully!"
""")
    custom_script.chmod(0o755)
    
    # Create a simple data file for the script to use
    data_file = job_dir / "sample_data.csv"
    data_file.write_text("id,value\\n1,100\\n2,200\\n3,300\\n")
    
    return str(job_dir)


def example_custom_bash_script_job():
    """Submit a job with a custom bash script file."""
    print("\\n=== Custom Bash Script Job (File) ===")
    
    job_dir = create_custom_bash_script_job()
    
    result = sj.submit_job(
        name="Custom Bash Script Job",
        code=job_dir,
        inputs={
            "TRAIN": f"{job_dir}/sample_data.csv"  # Local data file
        },
        run_script=f"{job_dir}/custom_run.sh",  # Path to custom script
        job_dir="./jobs",
        sync=True
    )
    
    print(f"Custom Script Job ID: {result.job_id}")
    print(f"Status: {result.status}")
    print(f"Duration: {result.duration:.2f}s")
    if result.output:
        print(f"Output:\\n{result.output}")
    if result.artifacts:
        print(f"Artifacts created: {len(result.artifacts)} files")
        for artifact in result.artifacts:
            print(f"  - {artifact}")
    
    return result.job_id


def example_inline_bash_script_job():
    """Submit a job with inline bash script content."""
    print("\\n=== Inline Bash Script Job ===")
    
    data_dir = create_sample_data()
    
    # Define custom bash script inline
    inline_script = """#!/bin/bash
set -e

echo "[INLINE] Running inline bash script!"
echo "[INLINE] Available data: $TRAIN"
echo "[INLINE] Output goes to: $OUTPUT_DIR"

# Simple data processing with bash tools
if [ -f "$TRAIN" ]; then
    echo "[INLINE] Processing training data..."
    line_count=$(wc -l < "$TRAIN")
    echo "[INLINE] Training data has $line_count lines"
    
    # Create summary
    echo "Data Summary" > "$OUTPUT_DIR/data_summary.txt"
    echo "============" >> "$OUTPUT_DIR/data_summary.txt"
    echo "File: $TRAIN" >> "$OUTPUT_DIR/data_summary.txt"
    echo "Lines: $line_count" >> "$OUTPUT_DIR/data_summary.txt"
    echo "Processed at: $(date)" >> "$OUTPUT_DIR/data_summary.txt"
else
    echo "[INLINE] No training data found"
fi

# Create a simple result
echo '{"status": "completed", "type": "inline_bash", "message": "Inline script executed successfully"}' > "$OUTPUT_DIR/inline_results.json"

echo "[INLINE] Inline script completed!"
"""
    
    result = sj.submit_job(
        name="Inline Bash Script Job",
        code=data_dir,  # Use data directory as code directory
        inputs={
            "TRAIN": f"{data_dir}/train.csv"
        },
        run_script=inline_script,  # Inline script content
        job_dir="./jobs",
        sync=True
    )
    
    print(f"Inline Script Job ID: {result.job_id}")
    print(f"Status: {result.status}")
    print(f"Duration: {result.duration:.2f}s")
    if result.output:
        print(f"Output:\\n{result.output}")
    if result.artifacts:
        print(f"Artifacts created: {len(result.artifacts)} files")
        for artifact in result.artifacts:
            print(f"  - {artifact}")
    
    return result.job_id


def example_batch_jobs():
    """Submit multiple jobs as a batch."""
    print("\\n=== Batch Job Submission ===")
    
    # Simple batch script
    batch_script = """#!/bin/bash
set -e

echo "[BATCH] Installing Python dependencies..."
if [ -f "$CODE_DIR/requirements.txt" ]; then
    pip install -r "$CODE_DIR/requirements.txt"
fi

echo "[BATCH] Running Python analysis..."
python "$CODE_DIR/main.py"

echo "[BATCH] Batch job completed!"
"""
    
    # Create multiple small jobs
    jobs = []
    for i in range(3):
        jobs.append({
            "name": f"Batch Job {i+1}",
            "code": "./sample_jobs/python_job",
            "run_script": batch_script,
            "inputs": {
                "TRAIN": "syft://datasets/batch_train.csv",
                "TEST": f"syft://datasets/batch_test_{i}.csv"
            },
            "metadata": {"batch_index": i}
        })
    
    results = sj.submit_batch_jobs(jobs, job_dir="./jobs")
    
    print(f"Submitted {len(results)} batch jobs:")
    for i, result in enumerate(results):
        print(f"  Job {i+1}: {result.job_id} - {result.status} ({result.duration:.2f}s)")
    
    return [r.job_id for r in results]


def list_job_workspaces():
    """List all job workspaces and show the new structure."""
    print("\\n=== Job Workspaces (New Structure) ===")
    
    jobs_dir = Path("./jobs")
    if jobs_dir.exists():
        job_dirs = [d for d in jobs_dir.iterdir() if d.is_dir()]
        print(f"Found {len(job_dirs)} job workspaces:")
        for job_dir in job_dirs:
            print(f"  📁 {job_dir.name}:")
            # List contents
            for item in job_dir.iterdir():
                if item.is_file():
                    if item.name == "config.yaml":
                        print(f"     📄 {item.name} (job configuration)")
                    elif item.name == "run.sh":
                        print(f"     📄 {item.name} (generated bash script)")
                    else:
                        print(f"     📄 {item.name}")
                elif item.is_dir():
                    if item.name == "inputs":
                        print(f"     📁 {item.name}/ (resolved input data)")
                    elif item.name == "outputs":
                        print(f"     📁 {item.name}/ (job outputs)")
                    else:
                        print(f"     📁 {item.name}/")
    else:
        print("No jobs directory found")


def inspect_job_files():
    """Show the contents of generated config.yaml and run.sh files."""
    print("\\n=== Generated Job Files ===")
    
    jobs_dir = Path("./jobs")
    if jobs_dir.exists():
        job_dirs = [d for d in jobs_dir.iterdir() if d.is_dir()]
        if job_dirs:
            latest_job = max(job_dirs, key=lambda p: p.stat().st_mtime)
            print(f"Inspecting latest job: {latest_job.name}")
            
            # Show config.yaml
            config_file = latest_job / "config.yaml"
            if config_file.exists():
                print(f"\\n📄 config.yaml:")
                print("-" * 40)
                print(config_file.read_text())
            
            # Show run.sh
            run_file = latest_job / "run.sh" 
            if run_file.exists():
                print(f"\\n📄 run.sh:")
                print("-" * 40)
                print(run_file.read_text())
        else:
            print("No job directories found")
    else:
        print("No jobs directory found")


def cleanup():
    """Clean up sample files and directories."""
    print("\\n=== Cleanup ===")
    
    dirs_to_clean = ["./sample_data", "./sample_jobs"]
    
    for dir_path in dirs_to_clean:
        path = Path(dir_path)
        if path.exists():
            shutil.rmtree(path)
            print(f"Removed {dir_path}")


if __name__ == "__main__":
    print("Syft Job Submission System - Folder-based Examples")
    print("=" * 60)
    print("Jobs will be executed in local folders with syft:// URL support")
    print("=" * 60)
    
    try:
        # Test local folder-based job submission
        python_job_id = example_python_job()
        
        # Test Go job
        go_job_id = example_go_job()
        
        # Test job with setup
        setup_job_id = example_job_with_setup()
        
        # Test custom bash script jobs
        custom_script_job_id = example_custom_bash_script_job()
        
        # Test inline bash script
        inline_script_job_id = example_inline_bash_script_job()
        
        # Test batch jobs
        batch_job_ids = example_batch_jobs()
        
        # List all job workspaces
        list_job_workspaces()
        
        # Show generated job files
        inspect_job_files()
        
        print("\\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during examples: {e}")
    
    try:
        cleanup()
    except Exception as e:
        print(f"⚠️  Cleanup error: {e}")
    
    print("\\n" + "=" * 60)
    print("🎉 Bash-Driven Job Submission Examples Complete!")
    print("\\n📖 Key Features Demonstrated:")
    print("   • Simple job structure: config.yaml + run.sh")
    print("   • Bash-driven execution (no language-specific runner logic)")
    print("   • Environment variable injection (TRAIN, TEST, CODE_DIR, OUTPUT_DIR)")
    print("   • Multi-language support via generated bash scripts")
    print("   • Custom bash script inputs (file paths or inline content)")
    print("   • Automatic dependency installation")
    print("   • Job workspaces preserved for inspection")
    print("\\n💡 Usage:")
    print("   import syft_job as sj")
    print("   result = sj.submit_job(name='my_job', code='./my_code', job_dir='./my_jobs')")
    print("\\n📁 Each job creates:")
    print("   job-{id}/")
    print("   ├── config.yaml    # Job configuration")
    print("   ├── run.sh         # Generated bash script")
    print("   ├── inputs/        # Resolved input data")
    print("   └── outputs/       # Job outputs")