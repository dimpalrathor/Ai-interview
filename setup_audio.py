# [file name]: setup_audio.py

import os
import sys
import subprocess
import platform

def check_system_requirements():
    """Check system requirements for audio functionality"""
    print("🔍 Checking system requirements...")
    
    system = platform.system()
    print(f"Operating System: {system}")
    print(f"Python Version: {sys.version}")
    
    # Check for required packages
    required_packages = ['pyaudio', 'speechrecognition', 'pyttsx3']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    return missing_packages, system

def install_missing_packages(missing_packages, system):
    """Install missing audio packages"""
    if not missing_packages:
        print("✅ All required packages are installed")
        return True
    
    print(f"📦 Installing missing packages: {missing_packages}")
    
    for package in missing_packages:
        try:
            if package == 'pyaudio' and system == 'Windows':
                # Use pipwin for PyAudio on Windows
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin"])
                subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio"])
            else:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            
            print(f"✅ Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def setup_audio_environment():
    """Set up the complete audio environment"""
    print("🎵 Setting up audio environment for AI Interview Bot...")
    
    # Check requirements
    missing_packages, system = check_system_requirements()
    
    # Install missing packages
    if not install_missing_packages(missing_packages, system):
        print("❌ Failed to install all required packages")
        return False
    
    # Platform-specific instructions
    if system == "Windows":
        print("\n💡 Windows Audio Setup:")
        print("1. Ensure Windows Audio Service is running")
        print("2. Check microphone permissions in Settings > Privacy > Microphone")
        print("3. Test your microphone in Sound Settings")
    
    elif system == "Darwin":  # macOS
        print("\n💡 macOS Audio Setup:")
        print("1. Grant microphone permissions in System Preferences > Security & Privacy")
        print("2. Check sound output settings")
    
    elif system == "Linux":
        print("\n💡 Linux Audio Setup:")
        print("1. Install ALSA or PulseAudio if not present")
        print("2. Check microphone permissions")
        print("3. You may need to install: sudo apt-get install python3-pyaudio")
    
    # Test the audio system
    print("\n🔊 Testing audio system...")
    try:
        # Import and test the enhanced audio handler
        from utils.audio_utils import AudioHandler
        audio_handler = AudioHandler()
        
        if audio_handler.is_audio_available():
            print("✅ Audio system is ready!")
            
            # Run comprehensive test
            test_results = audio_handler.test_audio_system()
            
            if all(test_results.values()):
                print("🎉 All audio tests passed! Your system is fully configured.")
            else:
                print("⚠️ Some audio tests failed. Check the troubleshooting guide.")
            
            audio_handler.stop_all_speech()
            return True
        else:
            print("❌ Audio system is not available")
            return False
            
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        return False

def create_troubleshooting_guide():
    """Create a comprehensive troubleshooting guide"""
    guide = """
    🚨 Audio Troubleshooting Guide
    ==============================
    
    Common Issues and Solutions:
    
    1. 🔇 No Sound Output:
       - Check speaker/headphone connection
       - Ensure volume is not muted
       - Test system sounds
       - Restart audio services
    
    2. 🎤 Microphone Not Working:
       - Check microphone permissions
       - Ensure microphone is not muted
       - Test with system voice recorder
       - Try a different microphone
    
    3. ❌ Speech Recognition Errors:
       - Check internet connection (for Google recognition)
       - Speak clearly and slowly
       - Reduce background noise
       - Use headset microphone for better quality
    
    4. 🐍 Python Package Issues:
       - Reinstall required packages
       - Use virtual environment
       - Check Python version compatibility
    
    5. 🔄 Runtime Errors:
       - Restart the application
       - Reboot your computer
       - Update audio drivers
    
    Quick Fixes:
    - Run the audio setup script again
    - Test with different microphone
    - Check system audio settings
    - Ensure no other app is using microphone
    """
    
    with open("audio_troubleshooting_guide.txt", "w") as f:
        f.write(guide)
    
    print("📖 Troubleshooting guide created: audio_troubleshooting_guide.txt")

if __name__ == "__main__":
    print("🤖 AI Interview Bot - Audio Setup Utility")
    print("=" * 50)
    
    success = setup_audio_environment()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("You can now run the AI Interview Bot with full audio capabilities.")
    else:
        print("\n❌ Setup encountered issues.")
        create_troubleshooting_guide()
        print("Please check the troubleshooting guide and try again.")
