from models import db

class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    availability = db.Column(db.Text, nullable=True) # JSON string

    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'name': self.name,
            'specialty': self.specialty,
            'hospital_id': self.hospital_id,
            'bio': self.bio,
            'availability': json.loads(self.availability) if self.availability else {}
        }
