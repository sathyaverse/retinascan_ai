import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'retinascan-secret-key-2024')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-retinascan-secret')

    # SQLite Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'retinascan.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), 'reports')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'dcm', 'pdf', 'gif', 'tiff', 'webp', 'heic'}
    MAX_CONTENT_LENGTH = None  # No size limit


    # CNN Model
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'dr_model.h5')
    IMAGE_SIZE = (224, 224)

    # DR Severity Labels
    DR_CLASSES = [
        'No DR',
        'Mild DR',
        'Moderate DR',
        'Severe DR',
        'Proliferative DR'
    ]

    DR_DESCRIPTIONS = {
        'No DR': 'No signs of diabetic retinopathy detected.',
        'Mild DR': 'Microaneurysms only. Regular monitoring recommended.',
        'Moderate DR': 'More than just microaneurysms. Ophthalmology referral advised.',
        'Severe DR': 'Severe NPDR. Urgent ophthalmology referral required.',
        'Proliferative DR': 'Advanced stage with neovascularisation. Immediate treatment needed.'
    }

    DR_RISK_COLOR = {
        'No DR': 'green',
        'Mild DR': 'yellow',
        'Moderate DR': 'orange',
        'Severe DR': 'red',
        'Proliferative DR': 'darkred'
    }
