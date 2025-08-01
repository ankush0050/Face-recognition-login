# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-face-recognition-2024'
    DEBUG = True
    
    # Database configuration (we'll start with SQLite for development)
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///face_recognition.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    UPLOAD_FOLDER = 'backend/data/employee_photos'
    TEMP_FOLDER = 'backend/data/temp'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Face recognition settings
    FACE_RECOGNITION_TOLERANCE = 0.6
    MIN_CONFIDENCE_THRESHOLD = 0.7
    FACE_DETECTION_SCALE_FACTOR = 1.1
    MIN_NEIGHBORS = 5
    
    # Security settings
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    MAX_LOGIN_ATTEMPTS = 5
    
    # OpenCV Haar Cascade settings (for face detection)
    FACE_CASCADE_PATH = 'haarcascade_frontalface_default.xml'
    EYE_CASCADE_PATH = 'haarcascade_eye.xml'
    
    @staticmethod
    def init_app(app):
        """Initialize the Flask application with this config"""
        # Create necessary directories
        import os
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.TEMP_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler('logs/face_recognition.log', 
                                             maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'))
            app.logger.addHandler(file_handler)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
