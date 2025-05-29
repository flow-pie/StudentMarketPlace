# config.py
import os

class Config:
    # enviroment setup
    ENV = "development"
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.abspath('uploads')
    MEDIA_URL = '/media/'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'jfif', 'gif'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_DOMAINS = {
        'images.unsplash.com',
        'i.imgur.com',
        "upload.wikimedia.org",
        'student-Market-Place-domain.com'
    }


    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        app.config.update(
            UPLOAD_FOLDER=Config.UPLOAD_FOLDER,
            MAX_CONTENT_LENGTH=Config.MAX_CONTENT_LENGTH,
            MEDIA_URL=Config.MEDIA_URL
        )