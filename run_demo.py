#!/usr/bin/env python3
"""
Quick demo launcher for the coaching app frontend with authentication
"""
import subprocess
import sys
import os

def main():
    print("Starting Coaching App with Authentication...")
    print("This will redirect to the integrated app with login functionality.")
    
    # Run the integrated app
    try:
        subprocess.run([sys.executable, 'integrated_app.py'], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == '__main__':
    main()