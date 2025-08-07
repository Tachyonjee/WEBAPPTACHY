#!/usr/bin/env python3
"""
Startup script for the main coaching application
"""

from main import app

if __name__ == '__main__':
    print("Starting Main Coaching Application on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)