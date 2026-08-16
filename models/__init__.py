from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import models to register them with SQLAlchemy
from models.user import User
from models.scan import Scan
from models.hospital import Hospital
from models.doctor import Doctor
from models.appointment import Appointment
from models.audit_log import AuditLog
from models.family_member import FamilyMember

