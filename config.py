import os

class Config:
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Language support configuration
    SUPPORTED_LANGUAGES = {
        'python': True,
        'java': True,
        'cpp': True,
        'javascript': True,
        'html': True,
        'css': True,
        'php': False,  # Requires additional setup
        'ruby': False,  # Requires additional setup
    }
    
    # Compiler paths (can be overridden by environment variables)
    JAVA_COMPILER = os.environ.get('JAVA_COMPILER', 'javac')
    CPP_COMPILER = os.environ.get('CPP_COMPILER', 'g++')
    NODE_PATH = os.environ.get('NODE_PATH', 'node')