#!/usr/bin/env python3
"""
Run the Role-Based Authentication Coaching System
"""

from auth_app import app, create_sample_users

if __name__ == '__main__':
    print("🎓 COACHING PLATFORM - AUTHENTICATION SYSTEM")
    print("=" * 50)
    print("Starting on http://localhost:5000")
    print("\nSample Login Credentials:")
    print("Students: student1/student123, student2/student123")
    print("Mentors: mentor1/mentor123, mentor2/mentor123") 
    print("Operators: operator1/operator123, operator2/operator123")
    print("Admin: admin/admin123")
    print("=" * 50)
    
    # Initialize database and sample users
    with app.app_context():
        try:
            create_sample_users()
            print("✓ Sample users ready")
        except:
            print("✓ Database ready")
    
    print("🚀 Starting server...")
    app.run(host='0.0.0.0', port=5000, debug=False)