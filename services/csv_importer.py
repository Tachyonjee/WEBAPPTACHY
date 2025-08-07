import pandas as pd
import json
from io import StringIO
from extensions import db
from models.question import Question

class CSVImporter:
    """Service for importing questions from CSV/Excel files"""
    
    REQUIRED_COLUMNS = [
        'subject', 'chapter', 'topic', 'difficulty', 'question_text',
        'correct_answer'
    ]
    
    OPTIONAL_COLUMNS = [
        'optionA', 'optionB', 'optionC', 'optionD', 'hint', 'source'
    ]
    
    VALID_SUBJECTS = ['Physics', 'Chemistry', 'Biology', 'Mathematics']
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.processed_count = 0
        self.imported_count = 0
    
    def validate_and_preview(self, file_content, file_type='csv'):
        """
        Validate file content and return preview data
        
        Args:
            file_content: File content as bytes or string
            file_type: 'csv' or 'xlsx'
            
        Returns:
            {
                'is_valid': bool,
                'errors': list,
                'warnings': list,
                'preview': list,
                'total_rows': int
            }
        """
        self.errors = []
        self.warnings = []
        
        try:
            # Read file into DataFrame
            if file_type == 'csv':
                df = pd.read_csv(StringIO(file_content.decode('utf-8')))
            elif file_type in ['xlsx', 'xls']:
                df = pd.read_excel(file_content)
            else:
                self.errors.append("Unsupported file type")
                return self._get_validation_result(None)
        
        except Exception as e:
            self.errors.append(f"Error reading file: {str(e)}")
            return self._get_validation_result(None)
        
        # Validate structure
        if not self._validate_structure(df):
            return self._get_validation_result(None)
        
        # Validate data
        preview_data = self._validate_data(df)
        
        return self._get_validation_result(df, preview_data)
    
    def import_questions(self, file_content, file_type='csv', dry_run=False):
        """
        Import questions from file
        
        Args:
            file_content: File content as bytes or string
            file_type: 'csv' or 'xlsx'
            dry_run: If True, don't actually save to database
            
        Returns:
            {
                'success': bool,
                'imported_count': int,
                'errors': list,
                'warnings': list
            }
        """
        validation_result = self.validate_and_preview(file_content, file_type)
        
        if not validation_result['is_valid']:
            return {
                'success': False,
                'imported_count': 0,
                'errors': validation_result['errors'],
                'warnings': validation_result['warnings']
            }
        
        # Read file again (could optimize by caching)
        try:
            if file_type == 'csv':
                df = pd.read_csv(StringIO(file_content.decode('utf-8')))
            else:
                df = pd.read_excel(file_content)
        except Exception as e:
            return {
                'success': False,
                'imported_count': 0,
                'errors': [f"Error reading file: {str(e)}"],
                'warnings': []
            }
        
        # Import questions
        imported_count = 0
        
        for index, row in df.iterrows():
            try:
                question = self._create_question_from_row(row)
                
                if not dry_run:
                    db.session.add(question)
                
                imported_count += 1
            
            except Exception as e:
                self.errors.append(f"Row {index + 2}: {str(e)}")
        
        if not dry_run and imported_count > 0:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return {
                    'success': False,
                    'imported_count': 0,
                    'errors': [f"Database error: {str(e)}"],
                    'warnings': self.warnings
                }
        
        return {
            'success': len(self.errors) == 0,
            'imported_count': imported_count,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def _validate_structure(self, df):
        """Validate that all required columns are present"""
        missing_columns = []
        
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            self.errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            return False
        
        # Check for empty DataFrame
        if df.empty:
            self.errors.append("File contains no data rows")
            return False
        
        return True
    
    def _validate_data(self, df):
        """Validate data in each row and return preview"""
        preview_data = []
        
        for index, row in df.iterrows():
            row_errors = []
            row_warnings = []
            
            # Validate subject
            subject = str(row.get('subject', '')).strip()
            if subject not in self.VALID_SUBJECTS:
                row_errors.append(f"Invalid subject: {subject}")
            
            # Validate difficulty
            try:
                difficulty = int(row.get('difficulty', 0))
                if difficulty < 1 or difficulty > 5:
                    row_errors.append("Difficulty must be between 1 and 5")
            except (ValueError, TypeError):
                row_errors.append("Difficulty must be a number")
            
            # Validate required fields
            for field in ['chapter', 'topic', 'question_text', 'correct_answer']:
                value = str(row.get(field, '')).strip()
                if not value or value == 'nan':
                    row_errors.append(f"{field} is required")
            
            # Check for MCQ options
            has_options = any(
                str(row.get(f'option{opt}', '')).strip() and str(row.get(f'option{opt}', '')).strip() != 'nan'
                for opt in ['A', 'B', 'C', 'D']
            )
            
            if has_options:
                # Validate that all options are provided
                for opt in ['A', 'B', 'C', 'D']:
                    value = str(row.get(f'option{opt}', '')).strip()
                    if not value or value == 'nan':
                        row_warnings.append(f"Option{opt} is empty but other options are provided")
                
                # Validate correct answer is A, B, C, or D
                correct_answer = str(row.get('correct_answer', '')).strip().upper()
                if correct_answer not in ['A', 'B', 'C', 'D']:
                    row_warnings.append("For MCQ, correct_answer should be A, B, C, or D")
            
            # Add to preview
            preview_row = {
                'row_number': index + 2,  # Excel row number (1-indexed + header)
                'subject': subject,
                'chapter': str(row.get('chapter', '')).strip(),
                'topic': str(row.get('topic', '')).strip(),
                'difficulty': row.get('difficulty', ''),
                'question_text': str(row.get('question_text', ''))[:100] + '...' if len(str(row.get('question_text', ''))) > 100 else str(row.get('question_text', '')),
                'has_options': has_options,
                'errors': row_errors,
                'warnings': row_warnings
            }
            
            preview_data.append(preview_row)
            
            # Add to global errors
            for error in row_errors:
                self.errors.append(f"Row {index + 2}: {error}")
            
            for warning in row_warnings:
                self.warnings.append(f"Row {index + 2}: {warning}")
        
        return preview_data
    
    def _create_question_from_row(self, row):
        """Create a Question object from DataFrame row"""
        question = Question()
        
        # Required fields
        question.subject = str(row['subject']).strip()
        question.chapter = str(row['chapter']).strip()
        question.topic = str(row['topic']).strip()
        question.difficulty = int(row['difficulty'])
        question.question_text = str(row['question_text']).strip()
        question.correct_answer = str(row['correct_answer']).strip()
        
        # Optional fields
        if pd.notna(row.get('hint')):
            question.hint = str(row['hint']).strip()
        
        if pd.notna(row.get('source')):
            question.source = str(row['source']).strip()
        
        # Handle MCQ options
        options = {}
        for opt in ['A', 'B', 'C', 'D']:
            value = row.get(f'option{opt}')
            if pd.notna(value) and str(value).strip():
                options[opt] = str(value).strip()
        
        if options:
            question.options = options
        
        return question
    
    def _get_validation_result(self, df, preview_data=None):
        """Get formatted validation result"""
        return {
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'preview': preview_data or [],
            'total_rows': len(df) if df is not None else 0
        }

def get_sample_csv_template():
    """Get sample CSV template for questions"""
    return """subject,chapter,topic,difficulty,question_text,optionA,optionB,optionC,optionD,correct_answer,hint,source
Physics,Mechanics,Kinematics,2,"A car accelerates from rest at 2 m/s². What is its velocity after 5 seconds?",8 m/s,10 m/s,12 m/s,15 m/s,B,Use v = u + at,Sample Book
Mathematics,Algebra,Quadratic Equations,3,"Solve x² - 5x + 6 = 0",x = 2 or 3,x = 1 or 6,x = -2 or -3,x = 0 or 5,A,Factor the quadratic,Practice Set 1
Chemistry,Organic Chemistry,Alkanes,1,"What is the general formula for alkanes?",CnH2n+2,CnH2n,CnH2n-2,CnHn,A,,Standard Formula
Biology,Cell Biology,Cell Structure,2,"Which organelle is known as the powerhouse of the cell?",,,,,"Mitochondria",Think about energy production,Biology Textbook"""
