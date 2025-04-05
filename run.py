#!/usr/bin/env python
"""
Runner script for the budget application.
Makes it easier to run the app as a command-line tool.
"""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the main function from budget.main
try:
    from budget.main import main
except ImportError as e:
    print(f"Error importing budget module: {e}")
    print("Make sure all dependencies are installed and the project structure is correct.")
    sys.exit(1)

if __name__ == "__main__":
    # Skip the first argument (script name) and pass the rest to main
    exit_code = main(sys.argv[1:])
    sys.exit(exit_code)