#!/usr/bin/env python3
"""
Authentication Demo for Role-Based Coaching Platform
"""

import os
import sys
from auth_app import app, create_sample_users

def print_banner():
    print("\n" + "="*80)
    print("🎓 COACHING PLATFORM - AUTHENTICATION DEMO")
    print("="*80)
    print("Role-based authentication system with beautiful dashboards")
    print(f"Server starting on: http://0.0.0.0:5000")
    print("\n📝 SAMPLE LOGIN CREDENTIALS:")
    print("-" * 50)
    print("👥 STUDENTS (with progress tracking):")
    print("   • student1 / student123")
    print("   • student2 / student123")  
    print("   • student3 / student123")
    print("\n👨‍🏫 MENTORS (student management):")
    print("   • mentor1 / mentor123")
    print("   • mentor2 / mentor123")
    print("   • mentor3 / mentor123")
    print("\n⚙️  OPERATORS (content management):")
    print("   • operator1 / operator123")
    print("   • operator2 / operator123")
    print("\n🔧 ADMIN (system administration):")
    print("   • admin / admin123")
    print("\n" + "="*80)

def initialize_system():
    """Initialize the database and sample users"""
    with app.app_context():
        try:
            create_sample_users()
            print("✓ Database and sample users initialized")
        except Exception as e:
            print(f"✓ Sample users already exist: {str(e)[:50]}...")

def main():
    print_banner()
    initialize_system()
    print("🚀 Starting Flask server...")
    print("Press Ctrl+C to stop the server")
    print("="*80)
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()