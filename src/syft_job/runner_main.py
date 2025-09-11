#!/usr/bin/env python3
"""
SyftJob Runner - Monitors inbox folder for new jobs.
"""

import argparse
import sys
from pathlib import Path
from .job_runner import create_runner


def main():
    """Main entry point for syft-job-runner."""
    parser = argparse.ArgumentParser(
        description="SyftJob Runner - Monitors inbox folder for new jobs"
    )
    parser.add_argument(
        "--config", 
        required=True,
        help="Path to the config.json file"
    )
    parser.add_argument(
        "--poll-interval", 
        type=int, 
        default=5,
        help="How often to check for new jobs (in seconds, default: 5)"
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config).expanduser().resolve()
    if not config_path.exists():
        print(f"❌ Error: Config file not found: {config_path}")
        sys.exit(1)
    
    try:
        runner = create_runner(str(config_path), args.poll_interval)
        runner.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()