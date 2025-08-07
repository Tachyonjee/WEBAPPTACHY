/**
 * Practice Session JavaScript
 * Handles interactive practice functionality
 */

class PracticeSession {
    constructor() {
        this.sessionId = null;
        this.currentQuestion = null;
        this.sessionStats = {
            questionsAnswered: 0,
            correctAnswers: 0,
            startTime: null,
            questionStartTime: null
        };
        this.sessionTimer = null;
        this.questionTimer = null;
        this.selectedMode = null;
        this.selectedTopics = [];
        this.currentAttempt = 1;
        this.maxAttempts = 2;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Mode selection
        document.querySelectorAll('.mode-card').forEach(card => {
            card.addEventListener('click', () => this.selectMode(card.dataset.mode));
        });
        
        // Subject selection for topic loading
        document.querySelectorAll('input[name="subjects"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.loadTopicsForSubjects());
        });
        
        // Answer submission
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitAnswer());
        }
        
        // Skip question
        const skipBtn = document.getElementById('skipBtn');
        if (skipBtn) {
            skipBtn.addEventListener('click', () => this.skipQuestion());
        }
        
        // End session
        document.addEventListener('click', (e) => {
            if (e.target.closest('[onclick="endSession()"]')) {
                this.endSession();
            }
        });
    }
    
    selectMode(mode) {
        // Update UI
        document.querySelectorAll('.mode-card').forEach(card => {
            card.classList.remove('selected');
        });
        document.querySelector(`[data-mode="${mode}"]`).classList.add('selected');
        
        this.selectedMode = mode;
        
        setTimeout(() => {
            if (mode === 'adaptive') {
                // Adaptive mode can start immediately
                this.startAdaptiveSession();
            } else {
                // Show topic selection for other modes
                this.showTopicSelection();
            }
        }, 300);
    }
    
    showTopicSelection() {
        document.getElementById('modeSelection').classList.add('d-none');
        document.getElementById('topicSelection').classList.remove('d-none');
        
        // Show topic selection for topic mode
        if (this.selectedMode === 'topic') {
            document.getElementById('topicSelectionDiv').style.display = 'block';
        }
    }
    
    async loadTopicsForSubjects() {
        const selectedSubjects = Array.from(document.querySelectorAll('input[name="subjects"]:checked'))
            .map(cb => cb.value);
        
        if (selectedSubjects.length === 0) return;
        
        try {
            const response = await fetch('/api/questions/topics?' + 
                new URLSearchParams({ subjects: selectedSubjects.join(',') }));
            const data = await response.json();
            
            const topicSelect = document.getElementById('topicSelect');
            topicSelect.innerHTML = '';
            
            data.topics.forEach(topic => {
                const option = document.createElement('option');
                option.value = topic;
                option.textContent = topic;
                topicSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading topics:', error);
            PWA.showToast('Error loading topics', 'error');
        }
    }
    
    async startAdaptiveSession() {
        await this.startSession('adaptive', [], []);
    }
    
    async startPracticeSession() {
        const selectedSubjects = Array.from(document.querySelectorAll('input[name="subjects"]:checked'))
            .map(cb => cb.value);
        
        const selectedTopics = this.selectedMode === 'topic' 
            ? Array.from(document.getElementById('topicSelect').selectedOptions).map(opt => opt.value)
            : [];
        
        const deviceType = document.getElementById('deviceType').value;
        
        if (selectedSubjects.length === 0) {
            PWA.showToast('Please select at least one subject', 'warning');
            return;
        }
        
        await this.startSession(this.selectedMode, selectedSubjects, selectedTopics, deviceType);
    }
    
    async startSession(mode, subjects, topics, deviceType = 'personal') {
        try {
            const response = await fetch('/api/students/practice/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    mode,
                    subjects,
                    topics,
                    device_type: deviceType
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.sessionId = data.session_id;
                this.sessionStats.startTime = Date.now();
                this.showPracticeSession();
                this.startSessionTimer();
                await this.loadNextQuestion();
                
                // Lock orientation for mobile
                if (window.PWA) {
                    PWA.lockOrientation();
                }
            } else {
                PWA.showToast(data.message || 'Failed to start session', 'error');
            }
        } catch (error) {
            console.error('Error starting session:', error);
            PWA.showToast('Network error. Please try again.', 'error');
        }
    }
    
    showPracticeSession() {
        document.getElementById('modeSelection').classList.add('d-none');
        document.getElementById('topicSelection').classList.add('d-none');
        document.getElementById('practiceSession').classList.remove('d-none');
    }
    
    startSessionTimer() {
        this.sessionTimer = setInterval(() => {
            const elapsed = Date.now() - this.sessionStats.startTime;
            document.getElementById('sessionTimer').textContent = this.formatTime(elapsed);
        }, 1000);
    }
    
    startQuestionTimer() {
        this.sessionStats.questionStartTime = Date.now();
        
        this.questionTimer = setInterval(() => {
            const elapsed = Date.now() - this.sessionStats.questionStartTime;
            const timerElement = document.getElementById('questionTimer');
            timerElement.textContent = this.formatTime(elapsed);
            
            // Add warning/danger classes
            const seconds = Math.floor(elapsed / 1000);
            timerElement.className = 'timer';
            if (seconds > 120) {
                timerElement.classList.add('danger');
            } else if (seconds > 60) {
                timerElement.classList.add('warning');
            }
        }, 1000);
    }
    
    async loadNextQuestion() {
        this.showLoadingState(true);
        
        try {
            const response = await fetch(`/api/students/practice/${this.sessionId}/next`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.question) {
                this.currentQuestion = data.question;
                this.currentAttempt = 1;
                this.displayQuestion(data.question);
                this.startQuestionTimer();
            } else if (data.session_complete) {
                this.showSessionComplete(data.stats);
            } else {
                PWA.showToast('Failed to load question', 'error');
            }
        } catch (error) {
            console.error('Error loading question:', error);
            PWA.showToast('Network error loading question', 'error');
        } finally {
            this.showLoadingState(false);
        }
    }
    
    displayQuestion(question) {
        // Update question info
        document.getElementById('questionSubject').textContent = question.subject;
        document.getElementById('questionTopic').textContent = question.topic;
        document.getElementById('questionDifficulty').textContent = `Level ${question.difficulty}`;
        document.getElementById('questionText').innerHTML = question.question_text;
        
        // Update question number
        this.sessionStats.questionsAnswered++;
        document.getElementById('questionNumber').textContent = this.sessionStats.questionsAnswered;
        document.getElementById('currentQuestionNum').textContent = this.sessionStats.questionsAnswered;
        
        // Clear previous state
        document.getElementById('optionsContainer').classList.add('d-none');
        document.getElementById('textAnswerContainer').classList.add('d-none');
        document.getElementById('hintContainer').classList.add('d-none');
        document.getElementById('solutionContainer').classList.add('d-none');
        
        // Show appropriate answer interface
        if (question.options && Object.keys(question.options).length > 0) {
            this.displayMCQOptions(question.options);
        } else {
            this.displayTextAnswer();
        }
        
        // Update attempt info
        document.getElementById('attemptInfo').textContent = `Attempt ${this.currentAttempt} of ${this.maxAttempts}`;
        
        // Enable submit button
        document.getElementById('submitBtn').disabled = true;
    }
    
    displayMCQOptions(options) {
        const container = document.getElementById('optionsContainer');
        container.innerHTML = '';
        
        Object.entries(options).forEach(([key, value]) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-outline-light option-btn mb-2';
            button.innerHTML = `<strong>${key}.</strong> ${value}`;
            button.dataset.option = key;
            
            button.addEventListener('click', () => this.selectOption(button));
            container.appendChild(button);
        });
        
        container.classList.remove('d-none');
    }
    
    displayTextAnswer() {
        document.getElementById('textAnswerContainer').classList.remove('d-none');
        const textAnswer = document.getElementById('textAnswer');
        textAnswer.value = '';
        textAnswer.addEventListener('input', () => {
            document.getElementById('submitBtn').disabled = textAnswer.value.trim().length === 0;
        });
        textAnswer.focus();
    }
    
    selectOption(selectedButton) {
        // Remove selection from other buttons
        document.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline-light');
        });
        
        // Highlight selected option
        selectedButton.classList.remove('btn-outline-light');
        selectedButton.classList.add('btn-primary');
        
        // Enable submit button
        document.getElementById('submitBtn').disabled = false;
    }
    
    async submitAnswer() {
        const selectedOption = document.querySelector('.option-btn.btn-primary');
        const textAnswer = document.getElementById('textAnswer');
        
        let chosenAnswer = '';
        if (selectedOption) {
            chosenAnswer = selectedOption.dataset.option;
        } else if (textAnswer && textAnswer.value.trim()) {
            chosenAnswer = textAnswer.value.trim();
        } else {
            PWA.showToast('Please select an answer', 'warning');
            return;
        }
        
        const timeTaken = Math.floor((Date.now() - this.sessionStats.questionStartTime) / 1000);
        
        try {
            const response = await fetch(`/api/students/practice/${this.sessionId}/attempt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    question_id: this.currentQuestion.id,
                    chosen_answer: chosenAnswer,
                    time_taken: timeTaken
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.handleAnswerResult(data);
            } else {
                PWA.showToast(data.message || 'Failed to submit answer', 'error');
            }
        } catch (error) {
            console.error('Error submitting answer:', error);
            PWA.showToast('Network error submitting answer', 'error');
        }
    }
    
    handleAnswerResult(result) {
        clearInterval(this.questionTimer);
        
        // Update stats
        if (result.is_correct) {
            this.sessionStats.correctAnswers++;
            PWA.showToast('Correct! Well done!', 'success');
        } else {
            PWA.showToast(`Incorrect. The correct answer is ${result.correct_answer}`, 'error');
        }
        
        // Update UI stats
        document.getElementById('correctCount').textContent = this.sessionStats.correctAnswers;
        const accuracy = Math.round((this.sessionStats.correctAnswers / this.sessionStats.questionsAnswered) * 100);
        document.getElementById('accuracyPercent').textContent = `${accuracy}%`;
        
        // Show solution if available
        if (result.solution) {
            document.getElementById('solutionContent').innerHTML = result.solution;
            document.getElementById('solutionContainer').classList.remove('d-none');
        }
        
        // Handle next steps
        if (!result.is_correct && this.currentAttempt < this.maxAttempts) {
            // Allow retry
            this.currentAttempt++;
            document.getElementById('attemptInfo').textContent = `Attempt ${this.currentAttempt} of ${this.maxAttempts}`;
            document.getElementById('submitBtn').disabled = false;
            
            // Show hint if available
            if (this.currentQuestion.hint) {
                document.getElementById('hintText').textContent = this.currentQuestion.hint;
                document.getElementById('hintContainer').classList.remove('d-none');
            }
        } else {
            // Move to next question
            setTimeout(() => {
                this.loadNextQuestion();
            }, 3000);
        }
    }
    
    async skipQuestion() {
        if (confirm('Are you sure you want to skip this question?')) {
            clearInterval(this.questionTimer);
            await this.loadNextQuestion();
        }
    }
    
    async toggleBookmark() {
        if (!this.currentQuestion) return;
        
        try {
            const response = await fetch(`/api/students/bookmarks/${this.currentQuestion.id}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                const bookmarkBtn = document.getElementById('bookmarkBtn');
                const icon = bookmarkBtn.querySelector('i');
                
                if (data.bookmarked) {
                    icon.className = 'fas fa-bookmark';
                    PWA.showToast('Question bookmarked', 'success');
                } else {
                    icon.className = 'far fa-bookmark';
                    PWA.showToast('Bookmark removed', 'info');
                }
            }
        } catch (error) {
            console.error('Error toggling bookmark:', error);
        }
    }
    
    async askDoubt() {
        const doubt = prompt('What\'s your doubt about this question?');
        if (!doubt || !doubt.trim()) return;
        
        try {
            const response = await fetch('/api/students/doubts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    question_id: this.currentQuestion.id,
                    message: doubt.trim()
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                PWA.showToast('Doubt submitted successfully!', 'success');
            } else {
                PWA.showToast(data.message || 'Failed to submit doubt', 'error');
            }
        } catch (error) {
            console.error('Error submitting doubt:', error);
            PWA.showToast('Network error submitting doubt', 'error');
        }
    }
    
    async endSession() {
        if (confirm('Are you sure you want to end this practice session?')) {
            clearInterval(this.sessionTimer);
            clearInterval(this.questionTimer);
            
            try {
                const response = await fetch(`/api/students/practice/${this.sessionId}/end`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    this.showSessionComplete(data.stats);
                }
            } catch (error) {
                console.error('Error ending session:', error);
            }
            
            // Unlock orientation
            if (window.PWA) {
                PWA.unlockOrientation();
            }
        }
    }
    
    showSessionComplete(stats) {
        document.getElementById('practiceSession').classList.add('d-none');
        document.getElementById('sessionComplete').classList.remove('d-none');
        
        // Update final stats
        document.getElementById('finalQuestions').textContent = stats.total_questions || this.sessionStats.questionsAnswered;
        document.getElementById('finalCorrect').textContent = stats.correct_answers || this.sessionStats.correctAnswers;
        document.getElementById('finalAccuracy').textContent = 
            `${Math.round(((stats.correct_answers || this.sessionStats.correctAnswers) / (stats.total_questions || this.sessionStats.questionsAnswered)) * 100)}%`;
        document.getElementById('finalTime').textContent = this.formatTime(Date.now() - this.sessionStats.startTime);
        
        // Unlock orientation
        if (window.PWA) {
            PWA.unlockOrientation();
        }
    }
    
    showLoadingState(show) {
        const loadingState = document.getElementById('loadingState');
        const submitBtn = document.getElementById('submitBtn');
        
        if (show) {
            loadingState.classList.remove('d-none');
            submitBtn.disabled = true;
        } else {
            loadingState.classList.add('d-none');
        }
    }
    
    formatTime(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
}

// Global functions for onclick handlers
window.showModeSelection = function() {
    document.getElementById('modeSelection').classList.remove('d-none');
    document.getElementById('topicSelection').classList.add('d-none');
};

window.startPracticeSession = function() {
    if (window.practiceSession) {
        window.practiceSession.startPracticeSession();
    }
};

window.toggleBookmark = function() {
    if (window.practiceSession) {
        window.practiceSession.toggleBookmark();
    }
};

window.askDoubt = function() {
    if (window.practiceSession) {
        window.practiceSession.askDoubt();
    }
};

window.endSession = function() {
    if (window.practiceSession) {
        window.practiceSession.endSession();
    }
};

// Initialize practice session when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('practiceApp')) {
        window.practiceSession = new PracticeSession();
    }
});