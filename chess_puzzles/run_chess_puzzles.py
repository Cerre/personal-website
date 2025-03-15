#!/usr/bin/env python3
"""
Wrapper script to run the chess puzzles generator.
"""
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main module directly
from main import main

if __name__ == "__main__":
    # Run the main function
    sys.exit(main()) 