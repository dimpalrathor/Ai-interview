# [file name]: app.py

import streamlit as st
import json
import time
import os
import datetime
import tempfile
from models.interview_model import InterviewModel
from utils.audio_utils import AudioHandler
from utils.evaluation_utils import EvaluationReport

class InterviewBot:
    def __init__(self):
        self.model = InterviewModel()
        self.audio_handler = AudioHandler()
        self.session_data = {
            'questions': [],
            'current_question_index': 0,
            'question_limit': 5,
            'session_active': False,
            'session_id': None,
            'start_time': None,
            'end_time': None,
            'auto_speak': True,
            'last_spoken_question': None
        }
    
    def initialize_session(self, question_limit):
        session_id = f"INT-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_data = {
            'questions': [],
            'current_question_index': 0,
            'question_limit': question_limit,
            'session_active': True,
            'session_id': session_id,
            'start_time': time.time(),
            'end_time': None,
            'auto_speak': True,
            'last_spoken_question': None
        }
        
        # Start continuous listening if audio is available
        if self.audio_handler.is_audio_available():
            success = self.audio_handler.start_continuous_listening()
            if success:
                print("✅ Voice recording activated")
    
    def get_next_question(self):
        if len(self.session_data['questions']) >= self.session_data['question_limit']:
            return None
        
        used_questions = [q['question'] for q in self.session_data['questions']]
        question = self.model.get_question(used_questions)
        
        if question:
            question_data = {
                'question': question['question'],
                'category': question['category'],
                'user_answer': '',
                'evaluation': None,
                'timestamp': time.time(),
                'question_number': len(self.session_data['questions']) + 1,
                'expected_keywords': question.get('expected_keywords', []),
                'ideal_answer': question.get('ideal_answer', '')
            }
            self.session_data['questions'].append(question_data)
            return question_data
        return None
    
    def submit_answer(self, answer):
        if self.session_data['questions']:
            current_question = self.session_data['questions'][-1]
            current_question['user_answer'] = answer
            current_question['evaluation'] = self.model.evaluate_answer(
                current_question, answer
            )
    
    def end_session(self):
        self.session_data['session_active'] = False
        self.session_data['end_time'] = time.time()
        self.audio_handler.stop_continuous_listening()
        self.audio_handler.stop_all_speech()

def generate_html_report(session_data):
    """Generate simple HTML report"""
    try:
        stats = calculate_session_stats(session_data)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Interview Report - {session_data.get('session_id', 'N/A')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ background: #2c3e50; color: white; padding: 30px; border-radius: 10px; }}
                .score {{ font-size: 3em; color: #3498db; font-weight: bold; }}
                .question {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
                .good {{ border-left: 5px solid #27ae60; }}
                .average {{ border-left: 5px solid #f39c12; }}
                .poor {{ border-left: 5px solid #e74c3c; }}
                .keyword {{ display: inline-block; background: #ecf0f1; padding: 5px 10px; margin: 2px; border-radius: 3px; }}
                .matched {{ background: #d4edda; color: #155724; }}
                .missing {{ background: #f8d7da; color: #721c24; }}
                .ideal-answer {{ background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 AI Interview Performance Report</h1>
                <p>Session ID: {session_data.get('session_id', 'N/A')} | Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <div class="score">{stats.get('overall_score', 0)}/10</div>
                <h2>Performance Level: {stats.get('performance_level', 'N/A')}</h2>
                <p>Total Questions: {stats.get('total_questions', 0)} | Duration: {stats.get('duration_formatted', 'N/A')}</p>
            </div>
            
            <h2>Detailed Analysis</h2>
            {"".join([create_question_html(q, i) for i, q in enumerate(session_data.get('questions', []))])}
            
            <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <h3>📊 Performance Insights</h3>
                <p>This report was generated automatically by the AI Interview Bot. Keep practicing to improve your interview skills!</p>
            </div>
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        return f"<html><body><h1>Error generating report: {e}</h1></body></html>"

def create_question_html(question_data, index):
    """Create HTML for a single question"""
    eval_data = question_data.get('evaluation', {})
    score = eval_data.get('score', 0)
    
    if score >= 7:
        rating_class = "good"
    elif score >= 5:
        rating_class = "average"
    else:
        rating_class = "poor"
    
    matched_keywords = "".join([f'<span class="keyword matched">{kw}</span>' for kw in eval_data.get('matched_keywords', [])])
    missing_keywords = "".join([f'<span class="keyword missing">{kw}</span>' for kw in eval_data.get('missing_keywords', [])])
    
    ideal_answer = eval_data.get('ideal_answer', question_data.get('ideal_answer', 'No model answer available.'))
    
    return f"""
    <div class="question {rating_class}">
        <h3>Q{index + 1}: {question_data.get('question', 'N/A')}</h3>
        <p><strong>Your Answer:</strong> {question_data.get('user_answer', 'No answer provided')}</p>
        <p><strong>Score:</strong> {score}/10</p>
        <div>
            <strong>Matched Keywords:</strong><br>{matched_keywords if matched_keywords else 'None'}
        </div>
        <div>
            <strong>Missing Keywords:</strong><br>{missing_keywords if missing_keywords else 'None'}
        </div>
        <div class="ideal-answer">
            <strong>💡 Model Answer:</strong><br>{ideal_answer}
        </div>
    </div>
    """

def calculate_session_stats(session_data):
    """Calculate session statistics"""
    questions = session_data.get('questions', [])
    if not questions:
        return {}
    
    scores = [q.get('evaluation', {}).get('score', 0) for q in questions]
    overall_score = sum(scores) / len(scores) if scores else 0
    
    # Performance level
    if overall_score >= 8:
        performance_level = "Excellent"
    elif overall_score >= 6:
        performance_level = "Good"
    elif overall_score >= 4:
        performance_level = "Average"
    else:
        performance_level = "Needs Improvement"
    
    # Duration
    duration = session_data.get('end_time', time.time()) - session_data.get('start_time', time.time())
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    duration_formatted = f"{minutes}:{seconds:02d}"
    
    return {
        'overall_score': round(overall_score, 2),
        'performance_level': performance_level,
        'total_questions': len(questions),
        'duration_formatted': duration_formatted
    }

def ensure_directories():
    """Ensure required directories exist"""
    os.makedirs('models', exist_ok=True)
    os.makedirs('utils', exist_ok=True)
    os.makedirs('templates', exist_ok=True)

def main():
    st.set_page_config(
        page_title="AI Interview Bot", 
        page_icon="🤖", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize session state
    if 'bot' not in st.session_state:
        st.session_state.bot = InterviewBot()
    if 'audio_text' not in st.session_state:
        st.session_state.audio_text = ""
    if 'auto_listening' not in st.session_state:
        st.session_state.auto_listening = False
    if 'question_changed' not in st.session_state:
        st.session_state.question_changed = False
    
    bot = st.session_state.bot
    
    st.title("🎙️ AI Interview Bot")
    st.markdown("---")
    
    # Enhanced Sidebar
    with st.sidebar:
        st.header("⚙️ Session Configuration")
        
        # Audio Diagnostics Section
        st.subheader("🔊 Audio Status")
        if bot.audio_handler.is_audio_available():
            st.success("✅ Audio System: Fully Operational")
            
            # Audio test button
            if st.button("🔧 Test Audio System", use_container_width=True):
                with st.spinner("Testing audio components..."):
                    results = bot.audio_handler.test_audio_system()
                
                if all(results.values()):
                    st.success("🎉 All audio tests passed!")
                else:
                    st.error("❌ Some audio tests failed")
                    if not results['tts']:
                        st.error("Text-to-Speech issues detected")
                    if not results['microphone']:
                        st.error("Microphone issues detected")
                    if not results['speech_recognition']:
                        st.error("Speech recognition issues detected")
        else:
            st.error("❌ Audio System: Unavailable")
            st.info("""
            **Troubleshooting tips:**
            - Check microphone permissions
            - Ensure speakers are working
            - Restart the application
            - Try using headphones with mic
            """)
        
        if not bot.session_data['session_active']:
            question_limit = st.selectbox(
                "Number of Questions:",
                options=[5, 10, 15, 20],
                index=0
            )
            
            # Enhanced auto-speak settings
            auto_speak = st.checkbox("Auto-speak questions", value=True, 
                                   help="Questions will be spoken automatically when they appear")
            bot.session_data['auto_speak'] = auto_speak
            
            # Voice input preference
            voice_preferred = st.checkbox("Prefer voice answers", value=True,
                                        help="Automatically use voice input when available")
            st.session_state.voice_preferred = voice_preferred
            
            if st.button("🚀 Start New Interview Session", type="primary", use_container_width=True):
                bot.initialize_session(question_limit)
                st.session_state.auto_listening = True
                st.session_state.question_changed = True
                st.rerun()
        
        else:
            st.info("📊 Interview in Progress")
            progress = len(bot.session_data['questions']) / bot.session_data['question_limit']
            st.progress(progress)
            st.write(f"**Progress:** {len(bot.session_data['questions'])}/{bot.session_data['question_limit']} questions")
            
            # Live Audio Controls
            st.subheader("🎚️ Live Audio Controls")
            auto_speak = st.checkbox("Auto-speak questions", 
                                   value=bot.session_data.get('auto_speak', True),
                                   key="auto_speak_live")
            bot.session_data['auto_speak'] = auto_speak
            
            # Manual audio controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔊 Speak Current", use_container_width=True):
                    if bot.session_data['questions']:
                        current_q = bot.session_data['questions'][-1]['question']
                        bot.audio_handler.speak_text(current_q, priority=True)
            with col2:
                if st.button("🔇 Stop Audio", use_container_width=True):
                    bot.audio_handler.stop_all_speech()
            
            if st.button("⏹️ End Session Early", type="secondary", use_container_width=True):
                bot.end_session()
                st.session_state.auto_listening = False
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 💡 Enhanced Voice Tips")
        st.info("""
        - **Speak clearly** and at a moderate pace
        - **Wait for the question to finish** before answering
        - **Avoid background noise** for better recognition
        - **Use complete sentences** for accurate transcription
        - **Check the transcription** before submitting
        """)

    # Main content
    if not bot.session_data['session_active']:
        if bot.session_data['questions']:
            show_results(bot)
        else:
            show_welcome()
    else:
        conduct_enhanced_interview(bot)

def show_welcome():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 50px;'>
            <h1>🎯 Welcome to AI Interview Bot</h1>
            <p style='font-size: 18px; color: #666;'>
                Practice your interview skills with our AI-powered bot. 
                Get instant feedback and improve your performance!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 🚀 Enhanced Features:
        - **🔊 Smart Auto-spoken Questions**: Improved voice quality and timing
        - **🎤 Enhanced Voice Recording**: Better speech recognition accuracy
        - **📝 Flexible Input**: Switch between voice and text seamlessly
        - **📊 Real-time Evaluation**: Get instant feedback on your answers
        - **💡 Model Answers**: See ideal answers for each question
        - **🎯 Audio Diagnostics**: Built-in audio testing and troubleshooting
        
        ### 🎙️ How to use Voice Features:
        1. **Allow microphone access** when prompted
        2. **Speak clearly** into your microphone
        3. **Wait for transcription** to appear
        4. **Submit** when you're satisfied with your answer
        
        ### 🎯 Get Started:
        Use the sidebar to configure your interview session!
        """)

def conduct_enhanced_interview(bot):
    st.header("🎙️ Interview Session")
    
    # Enhanced question handling with better voice coordination
    need_new_question = (not bot.session_data['questions'] or 
                        bot.session_data['questions'][-1]['user_answer'])
    
    if need_new_question:
        next_question = bot.get_next_question()
        if not next_question:
            bot.end_session()
            st.session_state.auto_listening = False
            st.rerun()
            return
        else:
            st.session_state.question_changed = True
            # Clear previous audio transcription
            st.session_state.audio_text = ""
    
    current_question = bot.session_data['questions'][-1]
    
    # Enhanced auto-speak with better timing
    if (st.session_state.question_changed and 
        bot.session_data['auto_speak'] and 
        bot.audio_handler.is_audio_available()):
        
        # Wait for any previous speech to complete
        bot.audio_handler.wait_for_speech_completion(timeout=2)
        time.sleep(0.5)  # Brief pause
        
        # Speak the question with priority
        bot.audio_handler.speak_text(current_question['question'], priority=True)
        bot.session_data['last_spoken_question'] = current_question['question']
        st.session_state.question_changed = False
        
        # Visual indication
        st.success("🔊 Question spoken! You may now answer...")
    
    # Display current question with enhanced UI
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### ❓ Question {len(bot.session_data['questions'])}/{bot.session_data['question_limit']}")
        
        with st.container():
            st.info(f"**Category:** {current_question['category'].title()}")
            question_text = current_question['question']
            st.markdown(f"#### {question_text}")
            
            # Enhanced audio controls
            if bot.audio_handler.is_audio_available():
                audio_col1, audio_col2 = st.columns(2)
                with audio_col1:
                    if st.button("🔊 Speak Question Again", key="speak_again", use_container_width=True):
                        bot.audio_handler.speak_text(question_text, priority=True)
                with audio_col2:
                    if st.button("🎤 Test Microphone", key="test_mic", use_container_width=True):
                        with st.spinner("Listening... Speak now!"):
                            test_result = bot.audio_handler.listen_for_speech(timeout=5)
                            if test_result not in ["timeout", "unknown", "error"]:
                                st.success(f"✅ Microphone working! Heard: '{test_result}'")
                            else:
                                st.error("❌ Microphone test failed")
    
    with col2:
        st.markdown("### 🎯 Answer Input")
        
        # Smart input mode selection
        if bot.audio_handler.is_audio_available() and st.session_state.get('voice_preferred', True):
            default_mode = "Auto Voice"
        else:
            default_mode = "Text"
            
        answer_mode = st.radio("Input Method:", ["Auto Voice", "Text"], 
                             index=0 if default_mode == "Auto Voice" else 1,
                             horizontal=True)
    
    # Enhanced voice input processing
    if answer_mode == "Auto Voice" and bot.audio_handler.is_audio_available():
        st.markdown("### 🎤 Auto Voice Recording")
        
        # Voice status indicator
        if bot.audio_handler.is_listening:
            st.success("🎤 **Live - Speak your answer now...**")
        else:
            st.warning("⚠️ Voice recording not active")
        
        # Real-time audio transcription display
        audio_text = bot.audio_handler.get_audio_text()
        if audio_text:
            st.session_state.audio_text = audio_text
            st.success(f"🎯 **Captured:** {audio_text}")
        
        # Enhanced transcription area
        user_answer = st.text_area(
            "**Voice Transcription:**",
            value=st.session_state.audio_text,
            height=120,
            key="audio_transcription",
            placeholder="Your spoken answer will appear here automatically...\nSpeak clearly and in complete sentences for better accuracy."
        )
        
        # Smart submission controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("📤 Submit Voice Answer", type="primary", use_container_width=True):
                if user_answer and user_answer.strip():
                    bot.submit_answer(user_answer.strip())
                    st.session_state.audio_text = ""
                    st.session_state.question_changed = True
                    st.rerun()
                else:
                    st.warning("Please speak your answer first")
        
        with col2:
            if st.button("🔄 Clear Transcription", use_container_width=True):
                st.session_state.audio_text = ""
                st.rerun()
        
        with col3:
            if st.button("🎙️ Manual Record", use_container_width=True):
                with st.spinner("Recording... Speak now!"):
                    manual_result = bot.audio_handler.listen_for_speech(timeout=10)
                    if manual_result not in ["timeout", "unknown", "error"]:
                        st.session_state.audio_text = manual_result
                        st.rerun()
        
        # Auto-submit suggestion
        if user_answer and len(user_answer.split()) >= 3:
            st.info("💡 **Tip:** Click 'Submit Voice Answer' when you're finished speaking")
    
    else:
        # Text input fallback
        user_answer = st.text_area(
            "**Your Answer:**",
            placeholder="Type your answer here...\n\n💡 Provide detailed answers with relevant keywords for better scoring.",
            height=150,
            key=f"answer_{len(bot.session_data['questions'])}"
        )
        
        if st.button("📤 Submit Answer", type="primary", use_container_width=True):
            if user_answer.strip():
                bot.submit_answer(user_answer.strip())
                st.session_state.question_changed = True
                st.rerun()
            else:
                st.warning("Please provide an answer before submitting.")

def show_results(bot):
    st.header("📊 Interview Results")
    
    # Generate reports
    report = EvaluationReport(bot.session_data)
    stats = report.calculate_overall_stats()
    
    # Overall performance cards
    st.subheader("🎯 Overall Performance")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Score", f"{stats['overall_score']:.2f}/10")
    
    with col2:
        st.metric("Performance Level", stats['performance_level'])
    
    with col3:
        st.metric("Total Questions", stats['total_questions'])
    
    with col4:
        duration = stats['duration']
        st.metric("Session Duration", f"{duration/60:.1f} min")
    
    # Category scores
    if stats['category_scores']:
        st.subheader("📈 Category-wise Performance")
        
        for category, score in stats['category_scores'].items():
            score_percent = (score / 10) * 100
            st.write(f"**{category.title()}**")
            st.progress(score_percent / 100)
            st.write(f"Score: {score:.2f}/10")
    
    # Detailed questions analysis with model answers
    st.subheader("🔍 Detailed Question Analysis")
    
    for i, q_data in enumerate(bot.session_data['questions'], 1):
        with st.expander(f"Q{i}: {q_data['question']} (Score: {q_data['evaluation']['score']}/10)", expanded=(i==1)):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Your Answer:** {q_data['user_answer']}")
                
                eval_data = q_data['evaluation']
                st.write(f"**Keyword Score:** {eval_data['keyword_score']}/10")
                st.write(f"**Sentiment Score:** {eval_data['sentiment_score']}/10")
                st.write(f"**Completeness Score:** {eval_data['completeness_score']}/10")
                st.write(f"**Fluency Score:** {eval_data['fluency_score']}/10")
                
                # Display model answer
                st.markdown("---")
                st.subheader("💡 Model Answer")
                ideal_answer = eval_data.get('ideal_answer', q_data.get('ideal_answer', 'No model answer available.'))
                st.info(ideal_answer)
            
            with col2:
                if eval_data['matched_keywords']:
                    st.success(f"✅ **Matched Keywords:** {', '.join(eval_data['matched_keywords'])}")
                else:
                    st.warning("⚠️ No keywords matched")
                
                if eval_data['missing_keywords']:
                    st.error(f"❌ **Missing Keywords:** {', '.join(eval_data['missing_keywords'])}")
    
    # Report downloads
    st.markdown("---")
    st.subheader("📥 Download Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Text report
        text_report = report.generate_report_text()
        st.download_button(
            label="📄 Download Text Report",
            data=text_report,
            file_name=f"interview_report_{bot.session_data.get('session_id', 'session')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        # PDF report
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                temp_pdf_path = tmp_file.name
            
            success = report.generate_pdf_report(temp_pdf_path)
            
            if success and os.path.exists(temp_pdf_path):
                with open(temp_pdf_path, "rb") as f:
                    pdf_data = f.read()
                
                os.unlink(temp_pdf_path)
                
                st.download_button(
                    label="📊 Download PDF Report",
                    data=pdf_data,
                    file_name=f"interview_report_{bot.session_data.get('session_id', 'session')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.error("PDF generation failed")
        except Exception as e:
            st.error(f"PDF Error: {e}")
    
    with col3:
        # HTML Report
        html_report = generate_html_report(bot.session_data)
        st.download_button(
            label="🌐 Download HTML Report",
            data=html_report,
            file_name=f"interview_report_{bot.session_data.get('session_id', 'session')}.html",
            mime="text/html",
            use_container_width=True
        )
    
    # Voice feedback and new session
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if bot.audio_handler.is_audio_available():
            if st.button("🔊 Hear Performance Summary", use_container_width=True):
                summary = f"""
                Your overall performance score is {stats['overall_score']:.1f} out of 10. 
                This is rated as {stats['performance_level']}. 
                You answered {stats['total_questions']} questions.
                Keep practicing to improve your skills!
                """
                bot.audio_handler.speak_text(summary)
    
    with col2:
        if st.button("🔄 Start New Interview Session", type="primary", use_container_width=True):
            bot.session_data['questions'] = []
            st.session_state.auto_listening = False
            st.session_state.question_changed = False
            st.rerun()

if __name__ == "__main__":
    main()
