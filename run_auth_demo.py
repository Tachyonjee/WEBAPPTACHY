#!/usr/bin/env python3
"""
Authentication Demo App for Coaching Platform
Runs on port 5000 with role-based dashboards
"""

from auth_app import app, create_sample_users

def main():
    print("=" * 60)
    print("🎓 COACHING PLATFORM - AUTHENTICATION DEMO")
    print("=" * 60)
    print("Starting authentication-based coaching app on port 5000...")
    print()
    print("SAMPLE LOGIN CREDENTIALS:")
    print("-------------------------")
    print("👥 STUDENTS:")
    print("   • student1 / student123 (JEE target)")
    print("   • student2 / student123 (NEET target)")
    print("   • student3 / student123 (JEE target)")
    print()
    print("👨‍🏫 MENTORS:")
    print("   • mentor1 / mentor123 (Math specialist)")
    print("   • mentor2 / mentor123 (Physics specialist)")
    print("   • mentor3 / mentor123 (Chemistry specialist)")
    print()
    print("⚙️  OPERATORS:")
    print("   • operator1 / operator123 (Content team)")
    print("   • operator2 / operator123 (QC team)")
    print()
    print("🔧 ADMIN:")
    print("   • admin / admin123 (System administrator)")
    print()
    print("=" * 60)
    print("Access the app at: http://localhost:5000")
    print("=" * 60)
    print()

    # Create sample users if they don't exist
    with app.app_context():
        try:
            create_sample_users()
            print("✓ Sample users initialized successfully")
        except Exception as e:
            print(f"Note: {e}")

    # Start the app
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()