# SyftJob Testing Scripts

This folder contains all testing and demonstration scripts for the SyftJob system.

## Test Scripts

### Core Functionality Tests

- **`test_syftbox_workflow.py`** - Original test for basic job submission workflow
- **`test_jobs_property.py`** - Tests the original jobs property that scanned all datasites
- **`test_new_jobs_functionality.py`** - Comprehensive test for indexable jobs with approval workflow
- **`test_corrected_functionality.py`** - Tests corrected workflow (inbox → done)
- **`test_approval_verification.py`** - Verifies approved jobs visibility in jobs list

### Debugging Scripts

- **`debug_jobs.py`** - Debug script for troubleshooting jobs scanning issues

### Demo Scripts

- **`demo_jobs_property.py`** - Interactive demo of the jobs property
- **`demo_complete_new_functionality.py`** - Complete demo of new indexable functionality
- **`demo_corrected_workflow.py`** - Demo of corrected workflow (inbox → done)
- **`test_complete_demo.py`** - Complete system demo with multiple users
- **`test_runner_demo.py`** - Demo of job runner functionality

## Quick Test Commands

Run any test from the project root:

```bash
# Test basic workflow
uv run python testing/test_syftbox_workflow.py

# Test corrected functionality (inbox → done)
uv run python testing/test_corrected_functionality.py

# Run complete demo
uv run python testing/demo_corrected_workflow.py

# Test job runner
uv run python testing/test_runner_demo.py
```

## Test Categories

### 1. Job Submission Tests
- Basic job submission to user datasites
- Directory structure creation
- Job file generation (run.sh, config.yaml)

### 2. Jobs Property Tests
- Indexable jobs access (`jobs[0]`)
- Jobs list display and formatting
- Current user datasite scanning only

### 3. Job Approval Tests
- `accept_by_depositing_result()` functionality
- Job status transitions (inbox → done)
- Result file deposition in outputs directory
- Error handling for invalid operations

### 4. Job Runner Tests
- Inbox monitoring functionality
- New job detection and display
- Directory structure creation

### 5. Integration Tests
- Complete workflow from submission to completion
- Multiple jobs handling
- Cross-user job management

## Key Features Tested

✅ **Job Submission API**
- `submit_bash_job(user, job_name, script)`
- Automatic directory structure creation
- Proper file permissions (run.sh executable)

✅ **Indexable Jobs Property**
- `job_client.jobs` returns `JobsList`
- `jobs[0]`, `jobs[1]` indexing
- `for job in jobs` iteration
- Nice table display with status emojis

✅ **Job Completion Workflow**
- `jobs[0].accept_by_depositing_result(file_path)`
- Jobs move from 📥 inbox → 🎉 done
- Result files stored in `done/JOB_NAME/outputs/`
- Proper error handling for invalid states

✅ **Job Runner**
- Continuous inbox monitoring
- New job detection and display
- Directory structure management

## Directory Structure Tested

```
SyftBox/datasites/<user_email>/app_data/job/
├── inbox/           # New job submissions
├── approved/        # (Future: manual approval step)
└── done/            # Completed with results
    └── <JOB_NAME>/
        ├── run.sh
        ├── config.yaml
        └── outputs/
            └── <result_files>
```

## Configuration Used in Tests

All tests use temporary directories with this config structure:

```json
{
  "data_dir": "/tmp/test_env/SyftBox",
  "email": "admin@example.com",
  "server_url": "https://syftbox.net",
  "refresh_token": "test_token"
}
```
