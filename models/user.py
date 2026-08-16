from datetime import datetime
from flask_login import UserMixin
from models import db, bcrypt, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    diabetes_type = db.Column(db.String(50), nullable=True)
    hba1c = db.Column(db.Float, nullable=True)
    diabetes_duration = db.Column(db.Integer, nullable=True)
    bp_systolic = db.Column(db.Integer, nullable=True)
    bp_diastolic = db.Column(db.Integer, nullable=True)
    family_history = db.Column(db.Text, nullable=True) # JSON string
    otp_code = db.Column(db.String(10), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    phone_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    scans = db.relationship('Scan', backref='patient', lazy=True, foreign_keys='[Scan.user_id]')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'age': self.age,
            'gender': self.gender,
            'diabetes_type': self.diabetes_type,
            'hba1c': self.hba1c,
            'diabetes_duration': self.diabetes_duration,
            'bp_systolic': self.bp_systolic,
            'bp_diastolic': self.bp_diastolic,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%d %b %Y') if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.email}>'
