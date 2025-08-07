import os
import json
import logging
from datetime import datetime
from extensions import db
from models.llm_logs import LLMEvent

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM operations (OpenAI integration)"""
    
    def __init__(self):
        from config import Config
        self.api_key = Config.OPENAI_API_KEY
        self.enabled = Config.LLM_ENABLED
        
        if self.enabled and self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI package not installed. LLM features disabled.")
                self.enabled = False
        else:
            self.client = None
    
    def generate_solution(self, question, student_id=None):
        """
        Generate detailed solution for a question
        
        Args:
            question: Question object
            student_id: Student ID for logging (optional)
            
        Returns:
            {
                'success': bool,
                'solution': str,
                'explanation': str,
                'steps': list,
                'error': str (if failed)
            }
        """
        start_time = datetime.utcnow()
        
        # Log the request
        event = LLMEvent(
            student_id=student_id,
            question_id=question.id,
            event_type='solution_request',
            payload={'question_text': question.question_text}
        )
        db.session.add(event)
        db.session.commit()
        
        try:
            if not self.enabled or not self.client:
                # Return fallback solution
                solution = self._get_fallback_solution(question)
                self._log_response(event, solution, success=True, response_time=0)
                return solution
            
            # Prepare prompt
            prompt = self._create_solution_prompt(question)
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert tutor for JEE/NEET preparation. "
                        "Provide detailed, step-by-step solutions that help students understand concepts. "
                        "Always explain the reasoning behind each step. "
                        "Respond with JSON in this format: "
                        "{'solution': 'brief answer', 'explanation': 'detailed explanation', 'steps': ['step1', 'step2', ...]}"
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse response
            content = response.choices[0].message.content
            solution_data = json.loads(content)
            
            # Calculate response time
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'success': True,
                'solution': solution_data.get('solution', ''),
                'explanation': solution_data.get('explanation', ''),
                'steps': solution_data.get('steps', [])
            }
            
            # Log successful response
            self._log_response(event, result, success=True, response_time=response_time)
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating solution: {str(e)}")
            
            # Calculate response time
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Log error
            self._log_response(event, None, success=False, response_time=response_time, error=str(e))
            
            # Return fallback
            fallback = self._get_fallback_solution(question)
            fallback['error'] = 'LLM service unavailable'
            return fallback
    
    def generate_questions(self, topic, difficulty, count=5, subject=None):
        """
        Generate practice questions for a topic (future feature)
        
        Args:
            topic: Topic name
            difficulty: Difficulty level (1-5)
            count: Number of questions to generate
            subject: Subject name
            
        Returns:
            {
                'success': bool,
                'questions': list,
                'error': str (if failed)
            }
        """
        # Log the request
        event = LLMEvent(
            event_type='gen_question_request',
            payload={
                'topic': topic,
                'difficulty': difficulty,
                'count': count,
                'subject': subject
            }
        )
        db.session.add(event)
        db.session.commit()
        
        # TODO: Implement question generation
        # For now, return placeholder
        result = {
            'success': False,
            'questions': [],
            'error': 'Question generation not yet implemented'
        }
        
        self._log_response(event, result, success=False, response_time=0)
        return result
    
    def _create_solution_prompt(self, question):
        """Create prompt for solution generation"""
        prompt = f"Subject: {question.subject}\n"
        prompt += f"Chapter: {question.chapter}\n"
        prompt += f"Topic: {question.topic}\n"
        prompt += f"Difficulty: {question.difficulty}/5\n\n"
        prompt += f"Question: {question.question_text}\n\n"
        
        if question.options:
            options = question.get_options()
            for key, value in options.items():
                prompt += f"({key}) {value}\n"
            prompt += f"\nCorrect Answer: {question.correct_answer}\n\n"
        else:
            prompt += f"Answer: {question.correct_answer}\n\n"
        
        prompt += "Please provide a detailed solution with step-by-step explanation."
        
        return prompt
    
    def _get_fallback_solution(self, question):
        """Get fallback solution when LLM is not available"""
        solution = {
            'success': True,
            'solution': question.correct_answer,
            'explanation': 'Detailed explanation is currently unavailable.',
            'steps': []
        }
        
        if question.hint:
            solution['explanation'] = f"Hint: {question.hint}"
            solution['steps'] = [question.hint]
        
        return solution
    
    def _log_response(self, event, result, success=True, response_time=0, error=None):
        """Log LLM response"""
        try:
            event.success = success
            event.response_time_ms = response_time
            event.error_message = error
            
            if result:
                # Log response event
                response_event = LLMEvent(
                    student_id=event.student_id,
                    question_id=event.question_id,
                    event_type='solution_response',
                    payload=result,
                    success=success,
                    response_time_ms=response_time,
                    error_message=error
                )
                db.session.add(response_event)
            
            db.session.commit()
        
        except Exception as e:
            logger.error(f"Error logging LLM response: {str(e)}")

# Singleton instance
llm_service = LLMService()

def is_llm_enabled():
    """Check if LLM features are enabled"""
    return llm_service.enabled

def get_solution(question, student_id=None):
    """Wrapper function for getting question solutions"""
    return llm_service.generate_solution(question, student_id)
