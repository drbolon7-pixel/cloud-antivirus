import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///antivirus.db')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    JWT_EXPIRATION = 3600  # 1 hour
    
    # VirusTotal API (opsional)
    VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY', '')
    
    # ClamAV configuration
    CLAMAV_HOST = os.getenv('CLAMAV_HOST', 'localhost')
    CLAMAV_PORT = int(os.getenv('CLAMAV_PORT', 3310))
    
    # File upload limits
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'exe', 'dll', 'doc', 'docx', 'pdf', 'zip', 'rar', 'js', 'vbs', 'scr', 'com'}
