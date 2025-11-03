import json
import random
import re
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except:
    pass

class InterviewModel:
    def __init__(self):
        self.questions = self.load_questions()
        self.stop_words = set(stopwords.words('english'))
    
    def load_questions(self):
        questions = []
        try:
            with open('database.jsonl', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        question_data = json.loads(line)
                        # Ensure ideal_answer is included from database
                        if 'ideal_answer' not in question_data:
                            question_data['ideal_answer'] = self.get_ideal_answer(question_data['question'])
                        questions.append(question_data)
        except FileNotFoundError:
            # Create default questions if file doesn't exist
            questions = self.create_default_questions()
        except Exception as e:
            print(f"Error loading questions: {e}")
            questions = self.create_default_questions()
        return questions
    
    def get_ideal_answer(self, question):
        """Get ideal answer for a question based on the question content"""
        ideal_answers = {
            "What is your experience with Python programming?": "I have 3+ years of professional experience with Python programming. I've worked on web development using Django and Flask, data analysis with Pandas and NumPy, and automation scripts. I'm proficient in object-oriented programming, REST API development, and have experience with popular Python libraries for machine learning and data visualization.",
            
            "Tell me about your problem-solving approach.": "My problem-solving approach is systematic: First, I thoroughly understand the problem and requirements. Then I break it down into smaller, manageable parts. I research potential solutions, evaluate the best approach, implement it, and test thoroughly. I believe in continuous improvement and always document my solutions for future reference.",
            
            "How do you handle tight deadlines?": "I handle tight deadlines through effective prioritization and time management. I break projects into smaller tasks with clear milestones, use project management tools to track progress, and maintain open communication with stakeholders about progress and potential challenges. I focus on delivering the most critical features first while maintaining quality standards.",
            
            "What database technologies are you familiar with?": "I'm experienced with both SQL and NoSQL databases. For SQL, I've worked extensively with MySQL and PostgreSQL, including database design, optimization, and complex queries. For NoSQL, I have experience with MongoDB for document storage and Redis for caching. I'm also familiar with ORM tools like SQLAlchemy and Django ORM.",
            
            "Describe a challenging project you worked on.": "One challenging project was developing a real-time analytics platform that processed large volumes of data. The main challenge was ensuring data consistency while maintaining performance. I implemented a distributed caching system, optimized database queries, and used asynchronous processing. The solution improved processing speed by 70% while maintaining data accuracy.",
            
            "What is your understanding of machine learning?": "Machine learning involves training algorithms to identify patterns in data and make predictions or decisions without being explicitly programmed. I understand supervised learning (classification, regression), unsupervised learning (clustering, dimensionality reduction), and reinforcement learning. I have practical experience with model training, evaluation metrics, and deployment using frameworks like Scikit-learn and TensorFlow.",
            
            "How do you stay updated with new technologies?": "I stay updated through multiple channels: I follow tech blogs and newsletters, participate in online courses on platforms like Coursera, attend webinars and tech meetups, contribute to open-source projects, and regularly practice coding challenges. I also experiment with new technologies through personal projects to gain hands-on experience.",
            
            "Explain REST API principles.": "REST API principles include: 1) Statelessness - each request contains all necessary information, 2) Client-Server architecture - separation of concerns, 3) Cacheability - responses can be cached, 4) Uniform interface - consistent resource identification and manipulation, 5) Layered system - architecture can have multiple layers. REST APIs use standard HTTP methods (GET, POST, PUT, DELETE) and typically return data in JSON format.",
            
            "What is your greatest strength?": "My greatest strength is my ability to quickly learn and adapt to new technologies and environments. I'm also strong in analytical thinking and problem-solving, which allows me to break down complex problems and develop effective solutions. Additionally, I have excellent communication skills that help me collaborate effectively with team members and stakeholders.",
            
            "How do you handle constructive criticism?": "I view constructive criticism as valuable feedback for growth. I listen actively without being defensive, ask clarifying questions to fully understand the feedback, reflect on how I can improve, and create a concrete action plan. I believe continuous learning and improvement are essential for professional development and always appreciate feedback that helps me grow."
        }
        return ideal_answers.get(question, "A good answer should address all aspects of the question, provide specific examples where relevant, and demonstrate both knowledge and practical experience in the subject matter.")
    
    def create_default_questions(self):
        """Create default questions if database file doesn't exist"""
        default_questions = [
            {
                "question": "What is your experience with Python programming?", 
                "category": "technical", 
                "expected_keywords": ["python", "programming", "experience", "projects", "libraries", "development", "frameworks"],
                "ideal_answer": self.get_ideal_answer("What is your experience with Python programming?")
            },
            {
                "question": "Tell me about your problem-solving approach.", 
                "category": "behavioral", 
                "expected_keywords": ["problem", "solution", "approach", "analyze", "implement", "methodology", "systematic"],
                "ideal_answer": self.get_ideal_answer("Tell me about your problem-solving approach.")
            },
            {
                "question": "How do you handle tight deadlines?", 
                "category": "behavioral", 
                "expected_keywords": ["deadlines", "priority", "time management", "planning", "stress", "organization", "communication"],
                "ideal_answer": self.get_ideal_answer("How do you handle tight deadlines?")
            }
        ]
        
        # Save default questions to file WITH ideal_answer
        try:
            with open('database.jsonl', 'w', encoding='utf-8') as f:
                for q in default_questions:
                    # Include ideal_answer in the saved data
                    f.write(json.dumps(q) + '\n')
        except Exception as e:
            print(f"Warning: Could not create database file: {e}")
            
        return default_questions
    
    def get_question(self, used_questions=None):
        if used_questions is None:
            used_questions = []
        
        available_questions = [q for q in self.questions if q['question'] not in used_questions]
        
        if not available_questions:
            # If all questions used, start over
            available_questions = self.questions
        
        return random.choice(available_questions)
    
    def evaluate_answer(self, question, user_answer):
        if not user_answer:
            return self.create_empty_evaluation()
        
        # Simple keyword matching evaluation
        expected_keywords = question.get('expected_keywords', [])
        user_answer_lower = user_answer.lower()
        
        # Count matching keywords
        matched_keywords = [kw for kw in expected_keywords if kw in user_answer_lower]
        keyword_score = len(matched_keywords) / len(expected_keywords) if expected_keywords else 0
        
        # Sentiment analysis using TextBlob
        try:
            sentiment = TextBlob(user_answer).sentiment
            sentiment_score = (sentiment.polarity + 1) / 2  # Convert from [-1,1] to [0,1]
        except:
            sentiment_score = 0.5
        
        # Answer completeness (length check)
        word_count = len(user_answer.split())
        if word_count < 10:
            completeness_score = 0.3
        elif word_count < 25:
            completeness_score = 0.6
        elif word_count < 50:
            completeness_score = 0.8
        else:
            completeness_score = 1.0
        
        # Grammar and fluency (simple check)
        try:
            blob = TextBlob(user_answer)
            # Simple fluency measure based on sentence count and length
            sentences = blob.sentences
            if len(sentences) > 0:
                avg_sentence_length = sum(len(sentence.words) for sentence in sentences) / len(sentences)
                if avg_sentence_length < 5:
                    fluency_score = 0.4
                elif avg_sentence_length < 10:
                    fluency_score = 0.7
                else:
                    fluency_score = 0.9
            else:
                fluency_score = 0.5
        except:
            fluency_score = 0.5
        
        # Overall score (weighted average)
        overall_score = (
            keyword_score * 0.4 +
            sentiment_score * 0.2 +
            completeness_score * 0.2 +
            fluency_score * 0.2
        ) * 10
        
        # Include the ideal answer from the question data in the evaluation
        return {
            'score': round(overall_score, 2),
            'matched_keywords': matched_keywords,
            'missing_keywords': [kw for kw in expected_keywords if kw not in user_answer_lower],
            'keyword_score': round(keyword_score * 10, 2),
            'sentiment_score': round(sentiment_score * 10, 2),
            'completeness_score': round(completeness_score * 10, 2),
            'fluency_score': round(fluency_score * 10, 2),
            'word_count': word_count,
            'ideal_answer': question.get('ideal_answer', 'No model answer available.')  # Add this line
        }
    
    def create_empty_evaluation(self):
        """Create evaluation for empty answers"""
        return {
            'score': 0.0,
            'matched_keywords': [],
            'missing_keywords': [],
            'keyword_score': 0.0,
            'sentiment_score': 0.0,
            'completeness_score': 0.0,
            'fluency_score': 0.0,
            'word_count': 0,
            'ideal_answer': 'No model answer available.'
        }