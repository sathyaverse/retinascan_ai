from datetime import datetime
from models import db


class Scan(db.Model):
    __tablename__ = 'scans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    family_member_id = db.Column(db.Integer, db.ForeignKey('family_members.id'), nullable=True)

    family_member = db.relationship('FamilyMember', backref='scans', lazy=True)


    # Image paths
    original_image = db.Column(db.String(255), nullable=False)
    preprocessed_image = db.Column(db.String(255), nullable=True)
    gradcam_image = db.Column(db.String(255), nullable=True)

    # Prediction results
    predicted_class = db.Column(db.String(50), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    class_probabilities = db.Column(db.Text, nullable=True)  # JSON string

    # Multi-disease prediction columns (Multi-label classification results)
    is_glaucoma = db.Column(db.Boolean, default=False)
    glaucoma_prob = db.Column(db.Float, default=0.0)
    is_amd = db.Column(db.Boolean, default=False)
    amd_prob = db.Column(db.Float, default=0.0)
    is_dr = db.Column(db.Boolean, default=False)
    dr_prob = db.Column(db.Float, default=0.0)
    is_cataract = db.Column(db.Boolean, default=False)
    cataract_prob = db.Column(db.Float, default=0.0)
    is_normal = db.Column(db.Boolean, default=True)
    normal_prob = db.Column(db.Float, default=0.0)
    multi_disease_probabilities = db.Column(db.Text, nullable=True)  # Detailed JSON string

    # DICOM and HIS integration fields
    dicom_patient_id = db.Column(db.String(100), nullable=True)
    his_sync_status = db.Column(db.Enum('unsynced', 'synced', 'failed'), default='unsynced')
    his_fhir_id = db.Column(db.String(100), nullable=True)

    # Clinical markers detected
    microaneurysms = db.Column(db.Boolean, default=False)
    hemorrhages = db.Column(db.Boolean, default=False)
    hard_exudates = db.Column(db.Boolean, default=False)
    soft_exudates = db.Column(db.Boolean, default=False)
    neovascularization = db.Column(db.Boolean, default=False)

    # Second opinion and quality parameters
    second_opinion_class = db.Column(db.String(50), nullable=True)
    second_opinion_confidence = db.Column(db.Float, nullable=True)
    second_opinion_probabilities = db.Column(db.Text, nullable=True)
    second_opinion_model = db.Column(db.String(50), nullable=True)
    quality_score = db.Column(db.Float, nullable=True)
    quality_issues = db.Column(db.Text, nullable=True)

    # Doctor review/signoff parameters
    doctor_signature = db.Column(db.Text, nullable=True)
    doctor_signed_off = db.Column(db.Boolean, default=False)
    doctor_notes = db.Column(db.Text, nullable=True)
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)

    # Status
    status = db.Column(db.String(20), default='pending')
    admin_notes = db.Column(db.Text, nullable=True)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    validated_at = db.Column(db.DateTime, nullable=True)

    # Report
    report_path = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    eye_side = db.Column(db.String(20), default='Unknown')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'family_member_id': self.family_member_id,
            'original_image': self.original_image,
            'gradcam_image': self.gradcam_image,
            'predicted_class': self.predicted_class,
            'confidence': round(self.confidence * 100, 2) if self.confidence else None,
            'glaucoma_prob': round(self.glaucoma_prob * 100, 2) if self.glaucoma_prob else 0.0,
            'amd_prob': round(self.amd_prob * 100, 2) if self.amd_prob else 0.0,
            'dr_prob': round(self.dr_prob * 100, 2) if self.dr_prob else 0.0,
            'cataract_prob': round(self.cataract_prob * 100, 2) if self.cataract_prob else 0.0,
            'normal_prob': round(self.normal_prob * 100, 2) if self.normal_prob else 0.0,
            'dicom_patient_id': self.dicom_patient_id,
            'his_sync_status': self.his_sync_status,
            'status': self.status,
            'eye_side': self.eye_side,
            'second_opinion_class': self.second_opinion_class,
            'second_opinion_confidence': round(self.second_opinion_confidence * 100, 2) if self.second_opinion_confidence else None,
            'second_opinion_model': self.second_opinion_model,
            'quality_score': round(self.quality_score * 100, 2) if self.quality_score else None,
            'quality_issues': self.quality_issues,
            'doctor_signed_off': self.doctor_signed_off,
            'doctor_notes': self.doctor_notes,
            'assigned_doctor_id': self.assigned_doctor_id,
            'created_at': self.created_at.strftime('%d %b %Y, %I:%M %p')
        }

    def __repr__(self):
        return f'<Scan {self.id} - {self.predicted_class}>'
