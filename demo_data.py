"""
Demo data for Coaching App
This file provides sample data for demonstration purposes
"""

# Sample questions for demonstration
DEMO_QUESTIONS = [
    {
        "id": 1,
        "question_text": "What is the derivative of sin(x) with respect to x?",
        "options": {
            "A": "cos(x)",
            "B": "-cos(x)", 
            "C": "sin(x)",
            "D": "-sin(x)"
        },
        "correct_answer": "A",
        "subject": "Mathematics",
        "topic": "Calculus",
        "chapter": "Differentiation",
        "difficulty": 1,
        "hint": "Remember the basic derivative rules for trigonometric functions.",
        "solution": "The derivative of sin(x) is cos(x). This is a fundamental result in calculus.",
        "explanation": "Using the limit definition or standard derivative rules, d/dx[sin(x)] = cos(x)."
    },
    {
        "id": 2,
        "question_text": "Which of the following is NOT a greenhouse gas?",
        "options": {
            "A": "Carbon dioxide (CO₂)",
            "B": "Methane (CH₄)",
            "C": "Oxygen (O₂)",
            "D": "Nitrous oxide (N₂O)"
        },
        "correct_answer": "C",
        "subject": "Physics",
        "topic": "Environmental Physics",
        "chapter": "Climate Change",
        "difficulty": 2,
        "hint": "Think about which gases trap heat in the atmosphere versus those that don't.",
        "solution": "Oxygen (O₂) is not a greenhouse gas. While essential for life, it doesn't significantly absorb infrared radiation.",
        "explanation": "Greenhouse gases absorb and emit infrared radiation. O₂ doesn't have this property significantly."
    },
    {
        "id": 3,
        "question_text": "What is the molecular formula of glucose?",
        "options": {
            "A": "C₆H₁₂O₆",
            "B": "C₆H₁₀O₅",
            "C": "C₅H₁₀O₅",
            "D": "C₆H₁₄O₆"
        },
        "correct_answer": "A",
        "subject": "Chemistry",
        "topic": "Organic Chemistry",
        "chapter": "Carbohydrates",
        "difficulty": 1,
        "hint": "Glucose is a simple sugar with 6 carbon atoms.",
        "solution": "Glucose has the molecular formula C₆H₁₂O₆, making it a hexose sugar.",
        "explanation": "Glucose is a monosaccharide with 6 carbons, 12 hydrogens, and 6 oxygens."
    },
    {
        "id": 4,
        "question_text": "In which organelle does photosynthesis primarily occur?",
        "options": {
            "A": "Mitochondria",
            "B": "Nucleus",
            "C": "Chloroplast",
            "D": "Ribosome"
        },
        "correct_answer": "C",
        "subject": "Biology",
        "topic": "Cell Biology",
        "chapter": "Photosynthesis",
        "difficulty": 1,
        "hint": "Think about which organelle contains chlorophyll.",
        "solution": "Photosynthesis occurs in chloroplasts, which contain chlorophyll and other photosynthetic pigments.",
        "explanation": "Chloroplasts are specialized organelles in plant cells that capture light energy for photosynthesis."
    },
    {
        "id": 5,
        "question_text": "What is the acceleration due to gravity on Earth's surface?",
        "options": {
            "A": "9.8 m/s²",
            "B": "10.8 m/s²",
            "C": "8.8 m/s²",
            "D": "11.2 m/s²"
        },
        "correct_answer": "A",
        "subject": "Physics",
        "topic": "Mechanics",
        "chapter": "Gravitation",
        "difficulty": 1,
        "hint": "This is a fundamental constant in physics.",
        "solution": "The acceleration due to gravity at Earth's surface is approximately 9.8 m/s².",
        "explanation": "This value varies slightly with location but 9.8 m/s² is the standard approximation."
    }
]

# Demo student data
DEMO_STUDENT_DATA = {
    "id": 1,
    "name": "Demo Student",
    "email": "demo@example.com",
    "goal_exam": "JEE",
    "batch": "Demo Batch 2024",
    "streak": {
        "current_streak": 7,
        "best_streak": 15,
        "last_practice_date": "2024-08-07"
    },
    "points": {
        "points_total": 1250,
        "points_today": 45,
        "points_week": 280
    },
    "today_stats": {
        "attempts": 12,
        "correct": 9,
        "accuracy": 75.0
    },
    "week_stats": {
        "attempts": 68,
        "correct": 51,
        "accuracy": 75.0
    }
}

# Demo subjects and topics
DEMO_SUBJECTS = {
    "Mathematics": {
        "chapters": ["Algebra", "Calculus", "Trigonometry", "Coordinate Geometry", "Statistics"],
        "topics": {
            "Algebra": ["Linear Equations", "Quadratic Equations", "Polynomials"],
            "Calculus": ["Limits", "Differentiation", "Integration"],
            "Trigonometry": ["Basic Functions", "Identities", "Inverse Functions"]
        }
    },
    "Physics": {
        "chapters": ["Mechanics", "Thermodynamics", "Optics", "Electromagnetism"],
        "topics": {
            "Mechanics": ["Motion", "Forces", "Energy", "Momentum"],
            "Thermodynamics": ["Heat", "Temperature", "Laws of Thermodynamics"],
            "Optics": ["Ray Optics", "Wave Optics", "Optical Instruments"]
        }
    },
    "Chemistry": {
        "chapters": ["Atomic Structure", "Chemical Bonding", "Organic Chemistry", "Physical Chemistry"],
        "topics": {
            "Atomic Structure": ["Bohr Model", "Quantum Numbers", "Electronic Configuration"],
            "Organic Chemistry": ["Hydrocarbons", "Functional Groups", "Reactions"],
            "Physical Chemistry": ["Thermodynamics", "Kinetics", "Equilibrium"]
        }
    },
    "Biology": {
        "chapters": ["Cell Biology", "Genetics", "Ecology", "Human Physiology"],
        "topics": {
            "Cell Biology": ["Cell Structure", "Cell Division", "Photosynthesis"],
            "Genetics": ["Mendel's Laws", "DNA", "Protein Synthesis"],
            "Ecology": ["Ecosystems", "Biodiversity", "Environmental Issues"]
        }
    }
}

# Demo recommendations
DEMO_RECOMMENDATIONS = [
    {
        "message": "Focus on Calculus problems - your accuracy in this topic has improved by 15% this week!",
        "reason": "Performance analysis shows strong progress in differentiation",
        "type": "strength_building",
        "priority": "medium"
    },
    {
        "message": "Consider reviewing Organic Chemistry reactions - you've struggled with this topic recently.",
        "reason": "Low accuracy (45%) in last 5 attempts",
        "type": "weakness_improvement", 
        "priority": "high"
    },
    {
        "message": "Great streak! Try a mock test to evaluate your overall progress.",
        "reason": "7-day practice streak achieved",
        "type": "milestone_reward",
        "priority": "low"
    }
]

# Demo performance data for charts
DEMO_PERFORMANCE_DATA = {
    "subject_accuracy": {
        "Mathematics": 0.82,
        "Physics": 0.75,
        "Chemistry": 0.68,
        "Biology": 0.71
    },
    "weekly_timeline": {
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "values": [75, 78, 82, 79, 85, 88, 90]
    },
    "topic_performance": {
        "Calculus": 0.85,
        "Mechanics": 0.78,
        "Organic Chemistry": 0.65,
        "Cell Biology": 0.72,
        "Algebra": 0.80
    },
    "streak_data": {
        "dates": ["Aug 1", "Aug 2", "Aug 3", "Aug 4", "Aug 5", "Aug 6", "Aug 7"],
        "streaks": [1, 2, 3, 4, 5, 6, 7]
    }
}

def get_demo_question(question_id=None):
    """Get a demo question by ID or random"""
    if question_id:
        return next((q for q in DEMO_QUESTIONS if q["id"] == question_id), None)
    
    import random
    return random.choice(DEMO_QUESTIONS)

def get_demo_questions_by_subject(subject):
    """Get demo questions filtered by subject"""
    return [q for q in DEMO_QUESTIONS if q["subject"] == subject]

def get_demo_student_profile():
    """Get demo student profile data"""
    return DEMO_STUDENT_DATA

def get_demo_subjects():
    """Get list of demo subjects"""
    return list(DEMO_SUBJECTS.keys())

def get_demo_topics(subjects=None):
    """Get topics for given subjects"""
    if not subjects:
        # Return all topics
        all_topics = []
        for subject_data in DEMO_SUBJECTS.values():
            for topic_list in subject_data["topics"].values():
                all_topics.extend(topic_list)
        return list(set(all_topics))
    
    topics = []
    for subject in subjects:
        if subject in DEMO_SUBJECTS:
            for topic_list in DEMO_SUBJECTS[subject]["topics"].values():
                topics.extend(topic_list)
    
    return list(set(topics))

def get_demo_recommendations():
    """Get demo recommendations"""
    return DEMO_RECOMMENDATIONS

def get_demo_performance_data():
    """Get demo performance data for charts"""
    return DEMO_PERFORMANCE_DATA