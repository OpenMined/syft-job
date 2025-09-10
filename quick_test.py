#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, './src')

import syft_job as sj
from pathlib import Path

def quick_test():
    print("=== Quick Test: Custom Bash Script ===")
    
    # Create a simple test directory
    test_dir = Path("./quick_test_workspace")
    test_dir.mkdir(exist_ok=True)
    
    # Test with simple inline script
    inline_script = """#!/bin/bash
echo "Custom script working!"
echo "CODE_DIR: $CODE_DIR"  
echo "OUTPUT_DIR: $OUTPUT_DIR"
echo "SUCCESS" > "$OUTPUT_DIR/success.txt"
"""
    
    # Create a runner that doesn't cleanup
    from syft_job.runner import JobRunner
    runner = JobRunner(job_dir="./quick_test_workspace", cleanup=False)
    
    result = sj.submit_job(
        name="Quick Test",
        code="/tmp",
        run_script=inline_script,
        job_dir="./quick_test_workspace",
        local_runner=runner,
        sync=True
    )
    
    print(f"Status: {result.status}")
    print(f"Duration: {result.duration:.3f}s")
    print(f"Job ID: {result.job_id}")
    
    if result.output:
        print(f"Output:\n{result.output}")
    if result.error:
        print(f"Error:\n{result.error}")
    
    # Check if job directory exists and show structure
    job_workspace = test_dir / result.job_id
    if job_workspace.exists():
        print("\nWorkspace contents:")
        for item in job_workspace.rglob("*"):
            print(f"  {item}")
            
        # Show the generated run.sh
        run_script = job_workspace / "run.sh"
        if run_script.exists():
            print(f"\nGenerated run.sh:")
            print("-" * 30)
            print(run_script.read_text())

if __name__ == "__main__":
    quick_test()