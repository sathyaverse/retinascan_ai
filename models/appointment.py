from datetime import datetime
from models import db

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='confirmed', nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    patient_phone = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    token_number = db.Column(db.Integer, nullable=True)
    teleconsultation_link = db.Column(db.String(255), nullable=True)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('appointments', lazy=True))
    hospital_rel = db.relationship('Hospital', backref=db.backref('appointments', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.name if self.doctor else 'Unknown Doctor',
            'hospital_id': self.hospital_id,
            'hospital_name': self.hospital_rel.name if self.hospital_rel else 'Unknown Hospital',
            'date': self.date.strftime('%Y-%m-%d'),
            'time_slot': self.time_slot,
            'status': self.status,
            'patient_name': self.patient_name,
            'patient_phone': self.patient_phone,
            'notes': self.notes,
            'token_number': self.token_number,
            'teleconsultation_link': self.teleconsultation_link,
            'reminder_sent': self.reminder_sent,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
