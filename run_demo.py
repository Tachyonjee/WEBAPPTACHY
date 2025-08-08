#!/usr/bin/env python3
"""
Tachyon Institute Management System Launcher
"""
import subprocess
import sys
import os

def main():
    print("Starting Tachyon Institute Management System...")
    print("Comprehensive educational institute management platform.")
    
    # Run the Tachyon app
    try:
        subprocess.run([sys.executable, 'tachyon_app.py'], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == '__main__':
    main()