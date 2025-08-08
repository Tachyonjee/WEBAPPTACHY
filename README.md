# JEE/NEET Coaching Platform

A comprehensive coaching platform for JEE/NEET exam preparation with role-based authentication, interactive features, and modern web technologies.

## Features

### 🔐 Authentication System
- **Mandatory Login**: Secure authentication required before accessing any features
- **Role-Based Access Control**: Different dashboards for students, mentors, operators, and admin
- **Session Management**: Secure login/logout with session handling
- **PostgreSQL Backend**: Reliable database with user management

### 👨‍🎓 Student Features
- **Interactive Dashboard**: Gamification with points, streaks, and badges
- **Practice Sessions**: Adaptive question delivery with real-time feedback
- **Progress Tracking**: Detailed analytics and performance monitoring
- **Doubt Resolution**: Submit and track doubts with mentor support
- **Bookmarks**: Save important questions and topics
- **PWA Support**: Installable web app with offline capabilities

### 👩‍🏫 Mentor Features
- **Student Management**: Monitor assigned students' progress
- **Analytics Dashboard**: Performance insights and reporting
- **Doubt Resolution**: Respond to student queries
- **Subject Specialization**: Role-based mentor assignments

### 🛠️ Operator Features
- **Content Management**: Add and edit questions and materials
- **Quality Control**: Review and approve content
- **Bulk Upload**: CSV/XLSX import for questions
- **Student Analytics**: Monitor platform usage

### 👑 Admin Features
- **User Management**: Complete control over all user accounts
- **System Analytics**: Platform-wide statistics and reporting
- **Content Oversight**: Full content management capabilities
- **Role Assignment**: Manage user roles and permissions

## Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Production database
- **Werkzeug**: Security utilities for password hashing
- **Flask-Login**: Session management

### Frontend
- **Progressive Web App (PWA)**: Modern web app with offline support
- **Bootstrap 5**: Responsive UI framework
- **Chart.js**: Interactive charts and analytics
- **Service Worker**: Offline functionality and caching
- **Modern JavaScript**: ES6+ with modular architecture

### Features
- **Responsive Design**: Mobile-first responsive layouts
- **Dark Theme Support**: Modern UI with theme switching
- **Real-time Updates**: Interactive features with live data
- **Offline Support**: PWA capabilities for offline access
- **Push Notifications**: Engagement and reminder system

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Modern web browser

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd coaching-platform
   ```

2. **Set up environment variables**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost/coaching_db"
   export SESSION_SECRET="your-secret-key-here"
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python integrated_app.py
   ```

5. **Access the application**
   - Open http://localhost:3000
   - Use the demo credentials below for testing

## Demo Credentials

### Students
- **Username**: student1, **Password**: student123
- **Username**: student2, **Password**: student123
- **Username**: student3, **Password**: student123

### Mentors
- **Username**: mentor1, **Password**: mentor123
- **Username**: mentor2, **Password**: mentor123
- **Username**: mentor3, **Password**: mentor123

### Operators
- **Username**: operator1, **Password**: operator123
- **Username**: operator2, **Password**: operator123

### Admin
- **Username**: admin, **Password**: admin123

## Architecture

### Database Models
- **User**: Core user management with role-based permissions
- **StudentProgress**: Track student performance and gamification
- **Questions**: Question bank with categorization
- **Attempts**: Student attempt tracking and analytics
- **Doubts**: Student query and mentor response system
- **Bookmarks**: User-specific content bookmarking

### Authentication Flow
1. User visits any protected route
2. Automatic redirect to login page if not authenticated
3. Credential validation against PostgreSQL database
4. Role-based redirection to appropriate dashboard
5. Session management with secure logout

### Security Features
- **Password Hashing**: Werkzeug security for safe password storage
- **Session Management**: Flask sessions with secure configuration
- **CSRF Protection**: Built-in security measures
- **Role-based Authorization**: Decorator-based access control

## Development

### Running in Development Mode
```bash
python integrated_app.py
```

### Project Structure
```
├── integrated_app.py          # Main application with authentication
├── templates/                 # Jinja2 templates
│   ├── auth/                 # Authentication templates
│   ├── student/              # Student dashboard templates
│   ├── mentor/               # Mentor dashboard templates
│   ├── operator/             # Operator dashboard templates
│   ├── admin/                # Admin dashboard templates
│   └── shared/               # Shared template components
├── app/static/               # Static files (CSS, JS, images)
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript files
│   └── manifest.json         # PWA manifest
├── models/                   # Database models
├── controllers/              # Route controllers
├── services/                 # Business logic services
└── uploads/                  # File upload directory
```

### Key Files
- **integrated_app.py**: Main Flask application with authentication
- **run_demo.py**: Application launcher
- **replit.md**: Project documentation and architecture notes

## Progressive Web App (PWA)

The platform includes full PWA support:

- **Installable**: Add to home screen on mobile devices
- **Offline Support**: Service worker for offline functionality
- **Push Notifications**: Engagement and reminder system
- **Responsive Design**: Mobile-first approach
- **Fast Loading**: Optimized assets and caching

## Deployment

The application is designed for easy deployment on platforms like:
- Replit
- Heroku
- AWS
- DigitalOcean
- Any platform supporting Flask and PostgreSQL

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test thoroughly
4. Submit a pull request

## License

This project is proprietary software for educational purposes.

## Support

For questions and support, please contact the development team.

---

Built with ❤️ for JEE/NEET aspirants