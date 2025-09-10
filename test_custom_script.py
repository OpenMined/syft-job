#!/usr/bin/env python3

"""
Quick test of custom bash script functionality.
"""

import sys
import os
sys.path.insert(0, './src')

import syft_job as sj

def test_inline_bash_script():
    """Test inline bash script functionality."""
    print("\n=== Testing Inline Bash Script ===")
    
    inline_script = """#!/bin/bash
set -e

echo "[TEST] Custom inline script executing!"
echo "[TEST] CODE_DIR: $CODE_DIR"
echo "[TEST] OUTPUT_DIR: $OUTPUT_DIR"

# Create a simple output file
echo "Custom script executed successfully" > "$OUTPUT_DIR/test_output.txt"
echo '{"status": "success", "type": "inline_test"}' > "$OUTPUT_DIR/result.json"

echo "[TEST] Inline script completed!"
"""
    
    result = sj.submit_job(
        name="Test Inline Script",
        code="/tmp",  # Use a simple existing directory
        run_script=inline_script,
        job_dir="./test_jobs",
        sync=True
    )
    
    print(f"Job ID: {result.job_id}")
    print(f"Status: {result.status}")
    print(f"Duration: {result.duration:.2f}s")
    
    if result.output:
        print(f"Output:\n{result.output}")
    
    if result.error:
        print(f"Error:\n{result.error}")
    
    return result.status.value == "completed"

def test_file_based_bash_script():
    """Test file-based bash script functionality."""
    print("\n=== Testing File-based Bash Script ===")
    
    import tempfile
    from pathlib import Path
    
    # Create a temporary script file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write("""#!/bin/bash
set -e

echo "[TEST] File-based custom script executing!"
echo "[TEST] Environment variables available:"
env | grep -E "(CODE_DIR|OUTPUT_DIR)" | sort

# Create output
echo "File-based script executed successfully" > "$OUTPUT_DIR/file_test_output.txt"
echo '{"status": "success", "type": "file_test"}' > "$OUTPUT_DIR/file_result.json"

echo "[TEST] File-based script completed!"
""")
        script_path = f.name
    
    try:
        result = sj.submit_job(
            name="Test File Script",
            code="/tmp",  # Use a simple existing directory
            run_script=script_path,
            job_dir="./test_jobs",
            sync=True
        )
        
        print(f"Job ID: {result.job_id}")
        print(f"Status: {result.status}")
        print(f"Duration: {result.duration:.2f}s")
        
        if result.output:
            print(f"Output:\n{result.output}")
        
        if result.error:
            print(f"Error:\n{result.error}")
        
        return result.status.value == "completed"
    
    finally:
        # Clean up temporary file
        os.unlink(script_path)

if __name__ == "__main__":
    print("Testing Custom Bash Script Functionality")
    print("=" * 50)
    
    try:
        inline_success = test_inline_bash_script()
        file_success = test_file_based_bash_script()
        
        print(f"\n=== Test Results ===")
        print(f"Inline script test: {'✅ PASS' if inline_success else '❌ FAIL'}")
        print(f"File-based script test: {'✅ PASS' if file_success else '❌ FAIL'}")
        
        if inline_success and file_success:
            print("\n🎉 All tests passed! Custom bash script functionality is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the logs above.")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()