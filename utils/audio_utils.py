# [file name]: audio_utils.py
import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
import sys
import pyaudio
import platform

class AudioHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.tts_engine = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.speech_thread = None
        self.stop_speech = False
        self.speech_lock = threading.Lock()
        self.audio_available = False
        
        # Initialize audio components
        self.initialize_audio_components()
        
    def initialize_audio_components(self):
        """Initialize all audio components with enhanced error handling"""
        try:
            # Initialize TTS
            self.initialize_tts()
            
            # Initialize microphone
            self.initialize_microphone()
            
            # Start speech processing thread
            self.start_speech_processor()
            
            self.audio_available = True
            print("✅ Audio components initialized successfully")
            
        except Exception as e:
            print(f"❌ Audio initialization failed: {e}")
            self.audio_available = False
    
    def initialize_tts(self):
        """Initialize text-to-speech engine with enhanced settings"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            
            # Configure voice settings
            if voices:
                # Prefer female voices for better clarity
                preferred_voices = [
                    voice for voice in voices 
                    if any(keyword in voice.name.lower() for keyword in ['female', 'zira', 'karen', 'veena'])
                ]
                
                if preferred_voices:
                    self.tts_engine.setProperty('voice', preferred_voices[0].id)
                    print(f"✅ Using preferred voice: {preferred_voices[0].name}")
                else:
                    self.tts_engine.setProperty('voice', voices[0].id)
                    print(f"✅ Using default voice: {voices[0].name}")
            
            # Enhanced TTS settings
            self.tts_engine.setProperty('rate', 170)  # Optimal speaking rate
            self.tts_engine.setProperty('volume', 0.9)  # Maximum volume
            
            # Try to set pitch if available
            try:
                self.tts_engine.setProperty('pitch', 110)  # Slightly higher pitch for clarity
            except:
                pass  # Pitch not supported by all engines
            
        except Exception as e:
            print(f"❌ TTS initialization failed: {e}")
            self.tts_engine = None
            raise
    
    def initialize_microphone(self):
        """Initialize microphone with enhanced settings"""
        try:
            # List available microphones
            print("🔍 Scanning for microphones...")
            mic_list = sr.Microphone.list_microphone_names()
            print(f"Found {len(mic_list)} microphone(s)")
            
            # Try to find the best microphone
            best_mic_index = None
            preferred_keywords = ['microphone', 'mic', 'input', 'default', 'primary']
            
            for i, name in enumerate(mic_list):
                name_lower = name.lower()
                if any(keyword in name_lower for keyword in preferred_keywords):
                    best_mic_index = i
                    print(f"✅ Selected microphone: {name}")
                    break
            
            if best_mic_index is not None:
                self.microphone = sr.Microphone(device_index=best_mic_index)
            else:
                self.microphone = sr.Microphone()
                print("✅ Using default microphone")
            
            # Enhanced noise adjustment
            print("🎙️ Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                # Set optimal energy threshold
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
            
            print("✅ Microphone calibrated successfully")
            
        except Exception as e:
            print(f"❌ Microphone initialization failed: {e}")
            self.microphone = None
            raise
    
    def start_speech_processor(self):
        """Start dedicated thread for speech processing"""
        def speech_worker():
            while not self.stop_speech:
                try:
                    text = self.speech_queue.get(timeout=1)
                    if text is None:  # Stop signal
                        break
                    self._speak_text_safe(text)
                    self.speech_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Speech worker error: {e}")
        
        self.speech_thread = threading.Thread(target=speech_worker, daemon=True)
        self.speech_thread.start()
        print("✅ Speech processor started")
    
    def _speak_text_safe(self, text):
        """Safely speak text with enhanced error handling"""
        if not self.tts_engine or not text:
            return False
            
        with self.speech_lock:
            try:
                self.is_speaking = True
                
                # Stop any current speech
                self.tts_engine.stop()
                
                # Speak new text
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
                # Small delay to ensure clean transition
                time.sleep(0.1)
                
                return True
                
            except RuntimeError as e:
                if "run loop already started" in str(e):
                    # Handle TTS engine state issue
                    try:
                        self.tts_engine.endLoop()
                    except:
                        pass
                    # Reinitialize TTS
                    self.initialize_tts()
                    return self._speak_text_safe(text)
                else:
                    print(f"TTS RuntimeError: {e}")
                    return False
                    
            except Exception as e:
                print(f"Speech synthesis failed: {e}")
                # Attempt to reinitialize TTS
                try:
                    self.tts_engine = None
                    self.initialize_tts()
                except Exception as reinit_error:
                    print(f"TTS reinitialization failed: {reinit_error}")
                return False
                
            finally:
                self.is_speaking = False
    
    def speak_text(self, text, priority=False):
        """Queue text for speech synthesis with optional priority"""
        if not self.tts_engine or not text:
            return False
            
        try:
            if priority:
                # Clear queue for high-priority messages
                self.clear_speech_queue()
            
            self.speech_queue.put(text)
            return True
            
        except Exception as e:
            print(f"Error queuing speech: {e}")
            return False
    
    def clear_speech_queue(self):
        """Clear all pending speech requests"""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
    
    def listen_for_speech(self, timeout=10, phrase_time_limit=8):
        """Listen for speech with enhanced recognition"""
        if not self.microphone:
            return "error"
        
        try:
            print("🎤 Listening for speech...")
            with self.microphone as source:
                # Enhanced recognition settings
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            
            print("🔍 Processing speech...")
            
            # Try multiple recognition engines for better accuracy
            try:
                text = self.recognizer.recognize_google(audio, language='en-US')
            except:
                try:
                    text = self.recognizer.recognize_google(audio, language='en-IN')
                except:
                    text = self.recognizer.recognize_google(audio)
            
            print(f"✅ Recognized: {text}")
            return text.lower().strip()
            
        except sr.WaitTimeoutError:
            print("⏰ Listening timeout")
            return "timeout"
        except sr.UnknownValueError:
            print("❌ Speech not understood")
            return "unknown"
        except sr.RequestError as e:
            print(f"🌐 Speech recognition error: {e}")
            return "error"
        except Exception as e:
            print(f"⚠️ Unexpected error in speech recognition: {e}")
            return "error"
    
    def start_continuous_listening(self):
        """Start continuous listening with enhanced settings"""
        if not self.microphone:
            return False
        
        self.is_listening = True
        
        def listen_loop():
            while self.is_listening:
                try:
                    result = self.listen_for_speech(timeout=5, phrase_time_limit=6)
                    if result not in ["timeout", "unknown", "error"] and result:
                        self.audio_queue.put(result)
                    # Small delay to prevent CPU overload
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error in continuous listening: {e}")
                    time.sleep(0.5)
        
        thread = threading.Thread(target=listen_loop)
        thread.daemon = True
        thread.start()
        print("✅ Continuous listening started")
        return True
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        self.is_listening = False
        print("✅ Continuous listening stopped")
    
    def get_audio_text(self):
        """Get transcribed text from audio queue"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    def wait_for_speech_completion(self, timeout=10):
        """Wait for all queued speech to complete"""
        try:
            self.speech_queue.join()
            return True
        except Exception as e:
            print(f"Error waiting for speech completion: {e}")
            return False
    
    def test_audio_system(self):
        """Comprehensive audio system test"""
        print("🔊 Running audio system test...")
        
        results = {
            'tts': False,
            'microphone': False,
            'speech_recognition': False
        }
        
        # Test TTS
        try:
            if self.speak_text("Audio test one two three. System is working."):
                time.sleep(2)  # Wait for speech to complete
                results['tts'] = True
                print("✅ TTS test passed")
        except Exception as e:
            print(f"❌ TTS test failed: {e}")
        
        # Test microphone and speech recognition
        try:
            print("🎤 Speak something for microphone test...")
            test_result = self.listen_for_speech(timeout=5)
            if test_result not in ["timeout", "unknown", "error"]:
                results['speech_recognition'] = True
                results['microphone'] = True
                print("✅ Microphone and speech recognition test passed")
            else:
                print(f"❌ Speech recognition test failed: {test_result}")
        except Exception as e:
            print(f"❌ Microphone test failed: {e}")
        
        return results
    
    def is_audio_available(self):
        """Check if audio features are available"""
        return self.audio_available
    
    def stop_all_speech(self):
        """Stop all speech and cleanup"""
        self.stop_speech = True
        self.stop_continuous_listening()
        
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
        
        self.clear_speech_queue()
        print("✅ All audio stopped and cleaned up")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_all_speech()
