import os
from dotenv import load_dotenv

load_dotenv()

IS_VERCEL = os.environ.get('VERCEL') == '1' or 'VERCEL' in os.environ
BASE_DIR = os.path.dirname(__file__)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'retinascan-secret-key-2024')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-retinascan-secret')

    # SQLite Database & Storage paths
    if IS_VERCEL:
        db_path = '/tmp/retinascan.db'
        orig_db = os.path.join(BASE_DIR, 'retinascan.db')
        if os.path.exists(orig_db) and not os.path.exists(db_path):
            import shutil
            try:
                shutil.copyfile(orig_db, db_path)
            except Exception:
                pass
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
        UPLOAD_FOLDER = '/tmp/uploads'
        REPORTS_FOLDER = '/tmp/reports'
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            'DATABASE_URL',
            'sqlite:///' + os.path.join(BASE_DIR, 'retinascan.db')
        )
        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
        REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'dcm', 'pdf', 'gif', 'tiff', 'webp', 'heic'}
    MAX_CONTENT_LENGTH = None  # No size limit

    # CNN Model
    MODEL_PATH = os.path.join(BASE_DIR, 'models', 'dr_model.h5')

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
