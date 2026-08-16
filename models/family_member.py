from datetime import datetime
from models import db

class FamilyMember(db.Model):
    __tablename__ = 'family_members'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relation = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    diabetes_type = db.Column(db.String(50), nullable=True)
    hba1c = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'relation': self.relation,
            'age': self.age,
            'gender': self.gender,
            'diabetes_type': self.diabetes_type,
            'hba1c': self.hba1c,
            'created_at': self.created_at.strftime('%d %b %Y') if self.created_at else None
        }
