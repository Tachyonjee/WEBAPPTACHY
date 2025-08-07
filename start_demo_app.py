#!/usr/bin/env python3
"""
Fixed startup script for the demo application
"""

import sys
import os

# Ensure we're in the correct directory
os.chdir('.')

# Import and run the demo app
from run_demo import app

if __name__ == '__main__':
    print("Starting Coaching Demo Application on port 3000...")
    app.run(host='0.0.0.0', port=3000, debug=False)