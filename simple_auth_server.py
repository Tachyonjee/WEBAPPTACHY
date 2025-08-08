#!/usr/bin/env python3
"""
Simple Authentication Server for Testing
"""

import os
from auth_app import app, create_sample_users

def main():
    print("Starting Authentication Server...")
    
    # Initialize sample users
    with app.app_context():
        try:
            create_sample_users()
            print("Sample users ready")
        except:
            print("Sample users already exist")
    
    print("Server running on http://localhost:5000")
    print("Login credentials:")
    print("student1/student123, mentor1/mentor123, operator1/operator123, admin/admin123")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()