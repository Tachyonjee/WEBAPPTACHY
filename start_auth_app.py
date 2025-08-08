#!/usr/bin/env python3
"""
Startup script for the role-based authentication coaching app
"""

if __name__ == '__main__':
    from auth_app import app
    print("=== Starting Authentication-Based Coaching App ===")
    print("Available at: http://localhost:5000")
    print("Sample Login Credentials:")
    print("Students: student1/student123, student2/student123, student3/student123")
    print("Mentors: mentor1/mentor123, mentor2/mentor123, mentor3/mentor123") 
    print("Operators: operator1/operator123, operator2/operator123")
    print("Admin: admin/admin123")
    print("==================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)