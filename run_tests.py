#!/usr/bin/env python3
"""
Test runner script for Smart Dispatch AI.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py -v           # Verbose output
    python run_tests.py -k search    # Run tests matching 'search'
    python run_tests.py --cov        # Run with coverage report
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run pytest with appropriate arguments."""
    
    # Base pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Add any command line arguments
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    # Ensure we're in the project directory
    project_dir = Path(__file__).parent
    
    print("=" * 80)
    print("🧪 SMART DISPATCH AI - TEST SUITE")
    print("=" * 80)
    print(f"Project Directory: {project_dir}")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 80)
    print()
    
    # Run pytest
    try:
        result = subprocess.run(cmd, cwd=project_dir)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error running tests: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

