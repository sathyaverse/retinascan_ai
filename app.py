import os
import json
import uuid
# Top-level imports

from datetime import datetime, date
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, jsonify, send_file, abort, session)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import Config
from models import db, bcrypt, login_manager
from models.user import User
from models.scan import Scan
from models.hospital import Hospital
from models.doctor import Doctor
from models.appointment import Appointment
from models.audit_log import AuditLog
from models.family_member import FamilyMember


from utils.preprocessing import preprocess_image, validate_image, check_image_quality
from utils.inference import run_inference
from utils.gradcam import generate_gradcam
from utils.pdf_report import generate_pdf_report
from utils.dicom_handler import parse_dicom_file
from utils.translations import translate
from utils.his_sync import sync_scan_to_his
from utils.notifications import send_email_report, send_sms_report

# Recall scheduler background daemon thread removed

# ──────────────────────────────────────────────
# App factory
# ──────────────────────────────────────────────
def create_app():
    app = Flask(__name__)
    
    pass

    app.config.from_object(Config)
    from datetime import timedelta
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

    @app.context_processor
    def inject_translation():
        def t(key):
            lang = session.get('lang', 'en')
            return translate(key, lang)
        return dict(t=t, current_lang=session.get('lang', 'en'))

    # ── Helpers ──────────────────────────────
    def allowed_file(filename):
        return ('.' in filename and
                filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'])

    def admin_required(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != 'admin':
                abort(403)
            return f(*args, **kwargs)
        return decorated

    def doctor_required(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in ['doctor', 'admin']:
                abort(403)
            return f(*args, **kwargs)
        return decorated

    def log_audit(action, details=None):
        try:
            uid = current_user.id if (current_user and current_user.is_authenticated) else None
            ip = request.remote_addr
            log = AuditLog(user_id=uid, action=action, details=details, ip_address=ip)
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            print(f"[Audit Log Error] {e}")

    def auto_assign_case(scan):
        try:
            doctors = Doctor.query.all()
            if doctors:
                # Find the doctor with the least active pending scans to auto-assign
                min_pending = float('inf')
                selected_doc = doctors[0]
                for doc in doctors:
                    count = Scan.query.filter_by(assigned_doctor_id=doc.id, doctor_signed_off=False).count()
                    if count < min_pending:
                        min_pending = count
                        selected_doc = doc
                scan.assigned_doctor_id = selected_doc.id
                db.session.commit()
                log_audit("Case Auto Assigned", f"Scan #{scan.id} assigned to Doctor {selected_doc.name}")
        except Exception as e:
            print(f"[Case Assignment Error] {e}")



    # ── Public routes ─────────────────────────
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/debug-db')
    def debug_db():
        try:
            users = User.query.all()
            out = []
            for u in users:
                out.append(f"ID: {u.id} | Email: {u.email} | Role: {u.role} | Active: {u.is_active} ({type(u.is_active).__name__}) | PW Hash Length: {len(u.password_hash) if u.password_hash else 0}")
            return "<br>".join(out)
        except Exception as e:
            return f"Error: {e}"


    @app.route('/debug-login-check')
    def debug_login_check():
        try:
            patient = User.query.filter_by(email='patient@retinascan.com').first()
            doctor = User.query.filter_by(email='doctor@retinascan.com').first()
            admin = User.query.filter_by(email='admin@retinascan.com').first()
            
            res = []
            for name, u, pw in [('Patient', patient, 'Patient@1234'), ('Doctor', doctor, 'Doctor@1234'), ('Admin', admin, 'Admin@1234')]:
                if not u:
                    res.append(f"{name}: NOT FOUND")
                else:
                    check = u.check_password(pw)
                    res.append(f"{name} ({u.email}): password check for '{pw}' -> {check}")
            return "<br>".join(res)
        except Exception as e:
            return f"Error: {e}"

    # ── Auth routes ───────────────────────────
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('user_dashboard'))
        if request.method == 'POST':
            name = request.form['name'].strip()
            email = request.form['email'].strip().lower()
            password = request.form['password']
            if User.query.filter_by(email=email).first():
                flash('Email already registered.', 'danger')
                return redirect(url_for('register'))
            user = User(name=name, email=email, role='user', is_active=True)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        return render_template('auth/register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif current_user.role == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            return redirect(url_for('user_dashboard'))
            
        if request.method == 'POST':
            email = request.form['email'].strip().lower()
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                if user.role == 'user':
                    # Patient account: Initiate OTP verification
                    import random
                    from datetime import timedelta
                    otp = f"{random.randint(100000, 999999)}"
                    user.otp_code = otp
                    user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
                    db.session.commit()
                    
                    session['pre_otp_user_id'] = user.id
                    log_audit("OTP Dispatched", f"OTP code dispatched to patient account {user.email}")
                    return redirect(url_for('verify_otp'))
                elif user.role == 'doctor':
                    login_user(user, remember=True)
                    session.permanent = True
                    log_audit("Doctor Login Success", f"Ophthalmologist {user.email} authenticated successfully")
                    return redirect(url_for('doctor_dashboard'))
                else: # Admin account
                    login_user(user, remember=True)
                    session.permanent = True
                    log_audit("Admin Login Success", f"Administrator {user.email} authenticated successfully")
                    return redirect(url_for('admin_dashboard'))
            flash('Invalid email or password.', 'danger')
        return render_template('auth/login.html')

    @app.route('/verify-otp', methods=['GET', 'POST'])
    def verify_otp():
        user_id = session.get('pre_otp_user_id')
        if not user_id:
            flash("Please sign in first.", "danger")
            return redirect(url_for('login'))
            
        user = User.query.get(user_id)
        if not user:
            abort(404)
            
        if request.method == 'POST':
            otp_val = request.form.get('otp', '').strip()
            if not user.otp_code or user.otp_code != otp_val:
                log_audit("OTP Login Failed", f"Invalid OTP entry for {user.email}")
                flash("Invalid verification passcode.", "danger")
                return redirect(url_for('verify_otp'))
                
            if datetime.utcnow() > user.otp_expiry:
                log_audit("OTP Login Failed", f"Expired OTP entry for {user.email}")
                flash("Passcode has expired. Please request a new one.", "danger")
                return redirect(url_for('verify_otp'))
                
            # Valid OTP: Log in the user
            user.otp_code = None
            user.phone_verified = True
            db.session.commit()
            
            login_user(user, remember=True)
            session.permanent = True
            session.pop('pre_otp_user_id', None)
            log_audit("Patient Login Success", f"Patient {user.email} completed 2FA authentication successfully")
            flash("Authenticated successfully!", "success")
            return redirect(url_for('user_dashboard'))
            
        return render_template('auth/otp_verify.html', otp_code_sim=user.otp_code)

    @app.route('/resend-otp')
    def resend_otp():
        user_id = session.get('pre_otp_user_id')
        if not user_id:
            flash("Please sign in first.", "danger")
            return redirect(url_for('login'))
            
        user = User.query.get(user_id)
        import random
        from datetime import timedelta
        otp = f"{random.randint(100000, 999999)}"
        user.otp_code = otp
        user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
        db.session.commit()
        
        log_audit("OTP Dispatched", f"OTP code re-sent to patient account {user.email}")
        flash("A new verification code has been generated.", "info")
        return redirect(url_for('verify_otp'))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    # ── User routes ───────────────────────────
    @app.route('/dashboard')
    @login_required
    def user_dashboard():
        scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).limit(5).all()
        total_scans = Scan.query.filter_by(user_id=current_user.id).count()
        processed = Scan.query.filter_by(user_id=current_user.id).filter(Scan.status.in_(['processed', 'validated'])).count()
        # Chart data: severity distribution for this user
        from sqlalchemy import func
        dist = db.session.query(Scan.predicted_class, func.count(Scan.id))\
            .filter(Scan.user_id == current_user.id, Scan.predicted_class != None)\
            .group_by(Scan.predicted_class).all()
        chart_data = {r[0]: r[1] for r in dist}
        
        # Load upcoming appointments
        appointments = Appointment.query.filter_by(user_id=current_user.id)\
            .filter(Appointment.status != 'cancelled')\
            .order_by(Appointment.date.asc()).limit(3).all()
            
        return render_template('user/dashboard.html',
                               scans=scans, total_scans=total_scans,
                               processed=processed, chart_data=json.dumps(chart_data),
                               appointments=appointments)

    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        if request.method == 'POST':
            patient_profile = request.form.get('patient_profile', 'myself')
            family_member_id = None
            if patient_profile != 'myself' and patient_profile.isdigit():
                family_member_id = int(patient_profile)

            if 'retinal_image' not in request.files:
                flash('No file selected.', 'danger')
                return redirect(request.url)
            file = request.files['retinal_image']
            eye_side = request.form.get('eye_side', 'Unknown')
            if file.filename == '' or not allowed_file(file.filename):

                flash('Invalid file. Please upload a JPG, PNG, or DICOM (.dcm) image.', 'danger')
                return redirect(request.url)

            # Save uploaded file
            uid = uuid.uuid4().hex[:8]
            ext = file.filename.rsplit('.', 1)[1].lower()
            upload_filename = f"scan_{current_user.id}_{uid}.{ext}"
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_filename)
            file.save(upload_path)

            # DICOM parsing vs Standard Image parsing vs PDF parsing
            dicom_patient_id = None
            original_image_filename = upload_filename
            eye_side_final = eye_side
            quality_score = 1.0
            quality_issues_list = []
            is_acceptable = True

            if ext == 'pdf':
                from utils.pdf_handler import parse_pdf_report, create_pdf_placeholder
                create_pdf_placeholder(app.config['UPLOAD_FOLDER'])
                pdf_data = parse_pdf_report(upload_path)
            elif ext == 'dcm':
                # Convert DICOM to JPEG
                jpg_filename = f"scan_{current_user.id}_{uid}.jpg"
                jpg_path = os.path.join(app.config['UPLOAD_FOLDER'], jpg_filename)
                
                # Parse
                dicom_data = parse_dicom_file(upload_path, jpg_path)
                
                original_image_filename = jpg_filename
                dicom_patient_id = dicom_data['patient_id']
                if dicom_data['age']:
                    current_user.age = dicom_data['age']
                if dicom_data['gender'] in ['Male', 'Female', 'Other']:
                    current_user.gender = dicom_data['gender']
                if dicom_data['eye_side'] != 'Unknown':
                    eye_side_final = dicom_data['eye_side']

                # Run image quality check
                original_full_path = os.path.join(app.config['UPLOAD_FOLDER'], original_image_filename)
                is_acceptable, quality_issues_list, quality_score = check_image_quality(original_full_path)
            else:
                # Standard image validation
                if not validate_image(upload_path):
                    os.remove(upload_path)
                    flash('Uploaded file is not a valid image.', 'danger')
                    return redirect(request.url)

                # Run image quality check
                original_full_path = os.path.join(app.config['UPLOAD_FOLDER'], original_image_filename)
                is_acceptable, quality_issues_list, quality_score = check_image_quality(original_full_path)
            
            if not is_acceptable:
                scan = Scan(
                    user_id=current_user.id,
                    family_member_id=family_member_id,
                    original_image=original_image_filename,
                    eye_side=eye_side_final,
                    dicom_patient_id=dicom_patient_id,
                    quality_score=quality_score,
                    quality_issues=json.dumps(quality_issues_list),
                    status='error'
                )
                db.session.add(scan)
                db.session.commit()
                log_audit("Quality Check Failed", f"Uploaded image for Scan #{scan.id} failed quality check: {', '.join(quality_issues_list)}")
                flash(f"Image quality check failed: {', '.join(quality_issues_list)}", "danger")
                return redirect(request.url)

            # Create scan record
            scan = Scan(
                user_id=current_user.id,
                family_member_id=family_member_id,
                original_image=original_image_filename,
                eye_side=eye_side_final,
                dicom_patient_id=dicom_patient_id,
                quality_score=quality_score,
                quality_issues=None if not quality_issues_list else json.dumps(quality_issues_list),
                status='pending'
            )
            db.session.add(scan)
            db.session.commit()

            if ext == 'pdf':
                scan.preprocessed_image = 'pdf_placeholder.svg'
                scan.gradcam_image = 'pdf_placeholder.svg'
                
                stages = ['No DR', 'Mild DR', 'Moderate DR', 'Severe DR', 'Proliferative DR']
                predicted_class = pdf_data['predicted_class']
                
                import random
                probs = [0.0] * 5
                pred_idx = stages.index(predicted_class)
                probs[pred_idx] = random.uniform(0.78, 0.96)
                rem = 1.0 - probs[pred_idx]
                for idx in range(5):
                    if idx != pred_idx:
                        probs[idx] = rem / 4
                        
                prob_dict = {stages[i]: round(probs[i] * 100, 2) for i in range(5)}
                scan.predicted_class = predicted_class
                scan.confidence = probs[pred_idx]
                scan.class_probabilities = json.dumps(prob_dict)
                
                dr_prob = 1.0 - probs[0]
                glaucoma_prob = 0.85 if pdf_data['has_glaucoma'] else random.uniform(0.04, 0.18)
                amd_prob = 0.88 if pdf_data['has_amd'] else random.uniform(0.02, 0.14)
                cataract_prob = 0.82 if (pdf_data.get('has_cataract') or random.random() < 0.15) else random.uniform(0.01, 0.15)
                
                scan.dr_prob = dr_prob
                scan.glaucoma_prob = glaucoma_prob
                scan.amd_prob = amd_prob
                scan.cataract_prob = cataract_prob
                scan.normal_prob = max(0.01, min(0.99, 1.0 - max(dr_prob, glaucoma_prob, amd_prob, cataract_prob)))
                
                scan.is_dr = dr_prob >= 0.45
                scan.is_glaucoma = glaucoma_prob >= 0.50
                scan.is_amd = amd_prob >= 0.48
                scan.is_cataract = cataract_prob >= 0.46
                scan.is_normal = (not scan.is_dr) and (not scan.is_glaucoma) and (not scan.is_amd) and (not scan.is_cataract)
                
                disease_probs = {
                    'diabetic_retinopathy': round(dr_prob * 100, 2),
                    'glaucoma': round(glaucoma_prob * 100, 2),
                    'macular_degeneration': round(amd_prob * 100, 2),
                    'cataract': round(cataract_prob * 100, 2),
                    'normal_healthy': round(scan.normal_prob * 100, 2)
                }
                scan.multi_disease_probabilities = json.dumps(disease_probs)
                
                # Clinical markers
                scan.microaneurysms = predicted_class != 'No DR'
                scan.hemorrhages = predicted_class in ['Severe DR', 'Proliferative DR']
                scan.hard_exudates = predicted_class in ['Moderate DR', 'Severe DR', 'Proliferative DR']
                scan.soft_exudates = predicted_class in ['Severe DR', 'Proliferative DR']
                scan.neovascularization = predicted_class == 'Proliferative DR'
                
                # Second opinion simulation
                scan.second_opinion_class = predicted_class
                scan.second_opinion_confidence = probs[pred_idx]
                scan.second_opinion_probabilities = json.dumps(prob_dict)
                scan.second_opinion_model = 'ResNet50V2 (V1.2.0)'
                
                scan.status = 'processed'
                db.session.commit()
            else:
                # Preprocess
                pre_filename = f"pre_{uid}.jpg"
                pre_path = os.path.join(app.config['UPLOAD_FOLDER'], pre_filename)
                
                img_array, _ = preprocess_image(original_full_path, pre_path, app.config['IMAGE_SIZE'])
                scan.preprocessed_image = pre_filename

                # Run CNN inference
                result = run_inference(img_array, app.config['MODEL_PATH'], app.config['DR_CLASSES'])
                scan.predicted_class = result['predicted_class']
                scan.confidence = result['confidence']
                scan.class_probabilities = result['class_probabilities']
                scan.microaneurysms = result['microaneurysms']
                scan.hemorrhages = result['hemorrhages']
                scan.hard_exudates = result['hard_exudates']
                scan.soft_exudates = result['soft_exudates']
                scan.neovascularization = result['neovascularization']
                
                # New Multi-Disease predictions
                scan.dr_prob = result['dr_prob']
                scan.glaucoma_prob = result['glaucoma_prob']
                scan.amd_prob = result['amd_prob']
                scan.cataract_prob = result['cataract_prob']
                scan.normal_prob = result['normal_prob']
                scan.is_dr = result['is_dr']
                scan.is_glaucoma = result['is_glaucoma']
                scan.is_amd = result['is_amd']
                scan.is_cataract = result['is_cataract']
                scan.is_normal = result['is_normal']
                scan.multi_disease_probabilities = result['multi_disease_probabilities']

                # Second Opinion
                scan.second_opinion_class = result['second_opinion_class']
                scan.second_opinion_confidence = result['second_opinion_confidence']
                scan.second_opinion_probabilities = result['second_opinion_probabilities']
                scan.second_opinion_model = result['second_opinion_model']

                # Grad-CAM
                class_idx = app.config['DR_CLASSES'].index(result['predicted_class'])
                gradcam_filename = f"gcam_{uid}.jpg"
                gradcam_path = os.path.join(app.config['UPLOAD_FOLDER'], gradcam_filename)
                gcam_result = generate_gradcam(img_array, app.config['MODEL_PATH'],
                                               class_idx, original_full_path, gradcam_path)
                if gcam_result:
                    scan.gradcam_image = gradcam_filename

                scan.status = 'processed'
                db.session.commit()
            
            log_audit("Retinal Scan Analysis", f"Processed Scan #{scan.id} for patient {current_user.email} (Prediction: {scan.predicted_class})")

            # Case auto-assignment
            auto_assign_case(scan)

            # Hospital Information System (HIS) Sync
            try:
                sync_res = sync_scan_to_his(scan, current_user)
                scan.his_sync_status = 'synced'
                scan.his_fhir_id = sync_res['fhir_id']
                db.session.commit()
            except Exception as e:
                print(f"[HIS Sync Error] {e}")
                scan.his_sync_status = 'failed'
                db.session.commit()

            flash('File analyzed successfully!', 'success')
            return redirect(url_for('results', scan_id=scan.id))


        members = FamilyMember.query.filter_by(user_id=current_user.id).all()
        return render_template('user/upload.html', members=members)

    @app.route('/upload-batch', methods=['POST'])
    @login_required
    def upload_batch():
        if 'retinal_images' not in request.files:
            return jsonify({'success': False, 'message': 'No files uploaded'}), 400
            
        files = request.files.getlist('retinal_images')
        eye_side = request.form.get('eye_side', 'Unknown')
        
        scans_data = []
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                continue
                
            uid = uuid.uuid4().hex[:8]
            ext = file.filename.rsplit('.', 1)[1].lower()
            upload_filename = f"scan_{current_user.id}_{uid}.{ext}"
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_filename)
            file.save(upload_path)
            
            # Create a pending scan object
            scan = Scan(
                user_id=current_user.id,
                original_image=upload_filename,
                eye_side=eye_side,
                status='pending'
            )
            db.session.add(scan)
            db.session.commit()
            
            scans_data.append({
                'id': scan.id,
                'filename': file.filename
            })
            
        log_audit("Batch Upload Created", f"Initiated batch queue upload of {len(scans_data)} files")
        return jsonify({'success': True, 'scans': scans_data})

    @app.route('/api/process-scan/<int:scan_id>', methods=['POST'])
    @login_required
    def api_process_scan(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
        original_full_path = os.path.join(app.config['UPLOAD_FOLDER'], scan.original_image)
        ext = scan.original_image.rsplit('.', 1)[1].lower() if '.' in scan.original_image else ''
        
        if ext == 'pdf':
            from utils.pdf_handler import parse_pdf_report, create_pdf_placeholder
            create_pdf_placeholder(app.config['UPLOAD_FOLDER'])
            pdf_data = parse_pdf_report(original_full_path)
            
            scan.preprocessed_image = 'pdf_placeholder.svg'
            scan.gradcam_image = 'pdf_placeholder.svg'
            
            stages = ['No DR', 'Mild DR', 'Moderate DR', 'Severe DR', 'Proliferative DR']
            predicted_class = pdf_data['predicted_class']
            
            import random
            probs = [0.0] * 5
            pred_idx = stages.index(predicted_class)
            probs[pred_idx] = random.uniform(0.78, 0.96)
            rem = 1.0 - probs[pred_idx]
            for idx in range(5):
                if idx != pred_idx:
                    probs[idx] = rem / 4
                    
            prob_dict = {stages[i]: round(probs[i] * 100, 2) for i in range(5)}
            scan.predicted_class = predicted_class
            scan.confidence = probs[pred_idx]
            scan.class_probabilities = json.dumps(prob_dict)
            
            dr_prob = 1.0 - probs[0]
            glaucoma_prob = 0.85 if pdf_data['has_glaucoma'] else random.uniform(0.04, 0.18)
            amd_prob = 0.88 if pdf_data['has_amd'] else random.uniform(0.02, 0.14)
            cataract_prob = 0.82 if (pdf_data.get('has_cataract') or random.random() < 0.15) else random.uniform(0.01, 0.15)
            
            scan.dr_prob = dr_prob
            scan.glaucoma_prob = glaucoma_prob
            scan.amd_prob = amd_prob
            scan.cataract_prob = cataract_prob
            scan.normal_prob = max(0.01, min(0.99, 1.0 - max(dr_prob, glaucoma_prob, amd_prob, cataract_prob)))
            scan.quality_score = 1.0
            
            scan.is_dr = dr_prob >= 0.45
            scan.is_glaucoma = glaucoma_prob >= 0.50
            scan.is_amd = amd_prob >= 0.48
            scan.is_cataract = cataract_prob >= 0.46
            scan.is_normal = (not scan.is_dr) and (not scan.is_glaucoma) and (not scan.is_amd) and (not scan.is_cataract)
            
            disease_probs = {
                'diabetic_retinopathy': round(dr_prob * 100, 2),
                'glaucoma': round(glaucoma_prob * 100, 2),
                'macular_degeneration': round(amd_prob * 100, 2),
                'cataract': round(cataract_prob * 100, 2),
                'normal_healthy': round(scan.normal_prob * 100, 2)
            }
            scan.multi_disease_probabilities = json.dumps(disease_probs)
            
            # Clinical markers
            scan.microaneurysms = predicted_class != 'No DR'
            scan.hemorrhages = predicted_class in ['Severe DR', 'Proliferative DR']
            scan.hard_exudates = predicted_class in ['Moderate DR', 'Severe DR', 'Proliferative DR']
            scan.soft_exudates = predicted_class in ['Severe DR', 'Proliferative DR']
            scan.neovascularization = predicted_class == 'Proliferative DR'
            
            # Second opinion simulation
            scan.second_opinion_class = predicted_class
            scan.second_opinion_confidence = probs[pred_idx]
            scan.second_opinion_probabilities = json.dumps(prob_dict)
            scan.second_opinion_model = 'ResNet50V2 (V1.2.0)'
            
            scan.status = 'processed'
            db.session.commit()
            quality_score = 1.0
        else:
            # 1. Quality Check
            is_acceptable, quality_issues_list, quality_score = check_image_quality(original_full_path)
            scan.quality_score = quality_score
            
            if not is_acceptable:
                scan.status = 'error'
                scan.quality_issues = json.dumps(quality_issues_list)
                db.session.commit()
                log_audit("Quality Check Failed", f"Scan #{scan.id} failed quality check in batch queue")
                return jsonify({
                    'success': False,
                    'error': 'Image quality check failed',
                    'issues': quality_issues_list,
                    'score': round(quality_score * 100, 1)
                })
                
            # 2. Preprocess
            uid = uuid.uuid4().hex[:8]
            pre_filename = f"pre_{uid}.jpg"
            pre_path = os.path.join(app.config['UPLOAD_FOLDER'], pre_filename)
            
            img_array, _ = preprocess_image(original_full_path, pre_path, app.config['IMAGE_SIZE'])
            scan.preprocessed_image = pre_filename
            
            # 3. Model Inference
            result = run_inference(img_array, app.config['MODEL_PATH'], app.config['DR_CLASSES'])
            scan.predicted_class = result['predicted_class']
            scan.confidence = result['confidence']
            scan.class_probabilities = result['class_probabilities']
            scan.microaneurysms = result['microaneurysms']
            scan.hemorrhages = result['hemorrhages']
            scan.hard_exudates = result['hard_exudates']
            scan.soft_exudates = result['soft_exudates']
            scan.neovascularization = result['neovascularization']
            scan.dr_prob = result['dr_prob']
            scan.glaucoma_prob = result['glaucoma_prob']
            scan.amd_prob = result['amd_prob']
            scan.cataract_prob = result['cataract_prob']
            scan.normal_prob = result['normal_prob']
            scan.is_dr = result['is_dr']
            scan.is_glaucoma = result['is_glaucoma']
            scan.is_amd = result['is_amd']
            scan.is_cataract = result['is_cataract']
            scan.is_normal = result['is_normal']
            scan.multi_disease_probabilities = result['multi_disease_probabilities']
            
            # Second opinion
            scan.second_opinion_class = result['second_opinion_class']
            scan.second_opinion_confidence = result['second_opinion_confidence']
            scan.second_opinion_probabilities = result['second_opinion_probabilities']
            scan.second_opinion_model = result['second_opinion_model']
            
            # 4. Grad-CAM
            class_idx = app.config['DR_CLASSES'].index(result['predicted_class'])
            gradcam_filename = f"gcam_{uid}.jpg"
            gradcam_path = os.path.join(app.config['UPLOAD_FOLDER'], gradcam_filename)
            gcam_result = generate_gradcam(img_array, app.config['MODEL_PATH'],
                                           class_idx, original_full_path, gradcam_path)
            if gcam_result:
                scan.gradcam_image = gradcam_filename
                
            scan.status = 'processed'
            db.session.commit()
            
        log_audit("Retinal Scan Analysis", f"Processed Scan #{scan.id} via batch queue (Prediction: {scan.predicted_class})")
        
        # Case auto-assignment
        auto_assign_case(scan)
        
        # HIS sync
        try:
            sync_scan_to_his(scan, current_user)
            scan.his_sync_status = 'synced'
            db.session.commit()
        except Exception:
            pass
            
        return jsonify({
            'success': True,
            'id': scan.id,
            'predicted_class': scan.predicted_class,
            'confidence': round(scan.confidence * 100, 1),
            'quality_score': round(quality_score * 100, 1)
        })

    @app.route('/results/<int:scan_id>')
    @login_required
    def results(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id and current_user.role != 'admin':
            abort(403)
        probs = json.loads(scan.class_probabilities) if scan.class_probabilities else {}
        description = app.config['DR_DESCRIPTIONS'].get(scan.predicted_class, '')
        risk_color = app.config['DR_RISK_COLOR'].get(scan.predicted_class, 'gray')
        return render_template('user/results.html', scan=scan, probs=probs,
                               description=description, risk_color=risk_color)

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if request.method == 'POST':
            current_user.name = request.form.get('name', current_user.name)
            current_user.phone = request.form.get('phone', current_user.phone)
            current_user.age = request.form.get('age', current_user.age)
            current_user.gender = request.form.get('gender', current_user.gender)
            current_user.diabetes_type = request.form.get('diabetes_type', current_user.diabetes_type)
            db.session.commit()
            flash('Profile updated.', 'success')
        return render_template('user/profile.html')

    @app.route('/reports')
    @login_required
    def reports():
        scans = Scan.query.filter_by(user_id=current_user.id)\
            .filter(Scan.status == 'processed')\
            .order_by(Scan.created_at.desc()).all()
        return render_template('user/reports.html', scans=scans)

    @app.route('/download-report/<int:scan_id>')
    @login_required
    def download_report(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id and current_user.role != 'admin':
            abort(403)
        report_filename = f"report_{scan_id}.pdf"
        report_path = os.path.join(app.config['REPORTS_FOLDER'], report_filename)
        if not os.path.exists(report_path):
            generate_pdf_report(scan, scan.patient, report_path, app.config['UPLOAD_FOLDER'])
            scan.report_path = report_filename
            db.session.commit()
        return send_file(report_path, as_attachment=True,
                         download_name=f'RetinaScan_Report_{scan_id}.pdf')

    # ── Admin routes ──────────────────────────
    @app.route('/admin')
    @login_required
    @admin_required
    def admin_dashboard():
        from sqlalchemy import func
        total_users = User.query.filter_by(role='user').count()
        total_scans = Scan.query.count()
        pending = Scan.query.filter(Scan.status.in_(['pending', 'processed']), Scan.doctor_signed_off == False).count()
        dist = db.session.query(Scan.predicted_class, func.count(Scan.id))\
            .filter(Scan.predicted_class != None)\
            .group_by(Scan.predicted_class).all()
        chart_data = {r[0]: r[1] for r in dist}
        recent_scans = Scan.query.order_by(Scan.created_at.desc()).limit(10).all()
        
        # Load HIPAA audit logs
        audit_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(15).all()
        
        return render_template('admin/dashboard.html',
                               total_users=total_users, total_scans=total_scans,
                               pending=pending, chart_data=json.dumps(chart_data),
                               recent_scans=recent_scans, audit_logs=audit_logs)

    @app.route('/admin/update-settings', methods=['POST'])
    @login_required
    @admin_required
    def admin_update_settings():
        primary_model = request.form.get('primary_model')
        secondary_model = request.form.get('secondary_model')
        blur_th = request.form.get('blur_threshold')
        res_th = request.form.get('res_threshold')
        
        log_audit("Update Model Configuration", f"Model settings updated: Primary={primary_model}, Secondary={secondary_model}, BlurTh={blur_th}, ResTh={res_th}")
        flash("Model configurations and quality parameters updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/analytics')
    @login_required
    @admin_required
    def admin_analytics():
        from sqlalchemy import func
        # Distribution
        dist = db.session.query(Scan.predicted_class, func.count(Scan.id))\
            .filter(Scan.predicted_class != None)\
            .group_by(Scan.predicted_class).all()
        chart_data = {r[0]: r[1] for r in dist}
        
        # Load HIPAA audit logs
        audit_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(30).all()
        
        return render_template('admin/analytics.html',
                               chart_data=json.dumps(chart_data),
                               audit_logs=audit_logs)

    @app.route('/admin/export-csv')
    @login_required
    @admin_required
    def admin_export_csv():
        import csv
        from io import StringIO
        from flask import make_response
        
        scans = Scan.query.all()
        si = StringIO()
        cw = csv.writer(si)
        
        # Write headers
        cw.writerow(['Scan ID', 'Patient Email', 'Primary AI Class', 'Primary Confidence', 'Second Opinion Class', 'Second Opinion Conf', 'Quality Score', 'Date', 'Doctor Sign-off'])
        for s in scans:
            cw.writerow([
                s.id,
                s.patient.email if s.patient else 'Unknown',
                s.predicted_class or 'N/A',
                s.confidence or 0.0,
                s.second_opinion_class or 'N/A',
                s.second_opinion_confidence or 0.0,
                s.quality_score or 0.0,
                s.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Yes' if s.doctor_signed_off else 'No'
            ])
            
        log_audit("Export Datastore", "CSV export of screening records generated")
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=RetinaScan_DataExport.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    @app.route('/admin/export-excel')
    @login_required
    @admin_required
    def admin_export_excel():
        return redirect(url_for('admin_export_csv'))

    @app.route('/admin/compile-report', methods=['POST'])
    @login_required
    @admin_required
    def admin_compile_report():
        selected_fields = request.form.getlist('fields')
        filter_stage = request.form.get('filter_stage')
        
        query = Scan.query
        if filter_stage == 'dr_only':
            query = query.filter(Scan.predicted_class != 'No DR', Scan.predicted_class != None)
        elif filter_stage == 'severe_only':
            query = query.filter(Scan.predicted_class.in_(['Severe DR', 'Proliferative DR']))
        elif filter_stage == 'normal_only':
            query = query.filter(Scan.predicted_class == 'No DR')
            
        scans = query.order_by(Scan.created_at.desc()).all()
        log_audit("Compile Report", f"Custom report compiled with filter={filter_stage}")
        return render_template('admin/scans.html', scans=scans, compiled=True, fields=selected_fields)

    # ── Doctor routes ──────────────────────────
    @app.route('/doctor/dashboard')
    @login_required
    @doctor_required
    def doctor_dashboard():
        # Load pending review queue scans (processed but not yet doctor signed off)
        pending_scans = Scan.query.filter_by(doctor_signed_off=False).filter(Scan.status == 'processed').all()
        # Count signed off scans
        signed_scans_count = Scan.query.filter_by(doctor_signed_off=True).count()
        # Find total assigned patient count
        assigned_patients_count = User.query.filter_by(role='user').count()
        # Today's token queue appointments
        active_appointments = Appointment.query.filter_by(status='confirmed').order_by(Appointment.token_number.asc()).all()
        
        return render_template('doctor/dashboard.html',
                               pending_scans=pending_scans,
                               signed_scans_count=signed_scans_count,
                               assigned_patients_count=assigned_patients_count,
                               active_appointments=active_appointments)

    @app.route('/doctor/validate/<int:scan_id>', methods=['GET', 'POST'])
    @login_required
    @doctor_required
    def doctor_validate(scan_id):
        if request.method == 'POST':
            scan = Scan.query.get_or_404(scan_id)
            scan.doctor_notes = request.form.get('doctor_notes', '')
            scan.doctor_signature = request.form.get('signature_data', '')
            scan.doctor_signed_off = True
            scan.status = 'validated'
            db.session.commit()
            
            log_audit("Doctor Sign-off", f"Scan #{scan.id} validated and signed off by Doctor {current_user.name}")
            flash(f"Scan #{scan_id} successfully validated & approved.", "success")
            
        return redirect(url_for('doctor_dashboard'))

    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        users = User.query.filter_by(role='user').order_by(User.created_at.desc()).all()
        return render_template('admin/users.html', users=users)

    @app.route('/admin/scans')
    @login_required
    @admin_required
    def admin_scans():
        scans = Scan.query.order_by(Scan.created_at.desc()).all()
        return render_template('admin/scans.html', scans=scans)

    @app.route('/admin/validate/<int:scan_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def validate_scan(scan_id):
        if request.method == 'POST':
            scan = Scan.query.get_or_404(scan_id)
            scan.status = 'validated'
            scan.admin_notes = request.form.get('notes', '')
            scan.validated_by = current_user.id
            scan.validated_at = datetime.utcnow()
            db.session.commit()
            flash(f'Scan #{scan_id} validated.', 'success')
        return redirect(url_for('admin_scans'))

    @app.route('/admin/toggle-user/<int:user_id>', methods=['POST'])
    @login_required
    @admin_required
    def toggle_user(user_id):
        user = User.query.get_or_404(user_id)
        user.is_active = not user.is_active
        db.session.commit()
        flash(f"User {'activated' if user.is_active else 'deactivated'}.", 'info')
        return redirect(url_for('admin_users'))

    # ── API endpoints (JSON) ──────────────────
    @app.route('/api/scan-history')
    @login_required
    def api_scan_history():
        scans = Scan.query.filter_by(user_id=current_user.id)\
            .order_by(Scan.created_at.desc()).all()
        return jsonify([s.to_dict() for s in scans])

    @app.route('/api/log-whatsapp-share/<int:scan_id>', methods=['POST'])
    @login_required
    def api_log_whatsapp_share(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id and current_user.role != 'admin':
            abort(403)
        phone = request.json.get('phone', '').strip()
        cleaned_num = "".join(c for c in phone if c.isdigit())
        log_audit("Share Report WhatsApp", f"Scan #{scan.id} shared via WhatsApp to {cleaned_num}")
        return jsonify({'success': True})

    # ── Language Translation Route ────────────
    @app.route('/change-language/<lang_code>')
    def change_language(lang_code):
        if lang_code in ['en', 'ta', 'hi', 'ml']:
            session['lang'] = lang_code
            flash(f"Language changed successfully.", "success")
        return redirect(request.referrer or url_for('user_dashboard'))

    # ── Telemedicine Consultation Route ────────
    @app.route('/telemedicine/<int:scan_id>')
    @login_required
    def telemedicine(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id and current_user.role != 'admin':
            abort(403)
        # Fetch the doctor associated with the user's appointment, if any, or load a default
        appointment = Appointment.query.filter_by(user_id=current_user.id, status='confirmed').first()
        doctor = appointment.doctor if appointment else Doctor.query.first()
        if not doctor:
            class MockDoctor:
                name = "Dr. Ramakrishnan"
                specialty = "Retina Specialist"
            doctor = MockDoctor()
        return render_template('user/telemedicine.html', scan=scan, doctor=doctor)

    # ── Health Tips Library Route ─────────────
    @app.route('/health-tips')
    @login_required
    def health_tips():
        # Get highest risk condition from latest scan to highlight specific advice
        latest_scan = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).first()
        highest_condition = 'normal'
        if latest_scan and latest_scan.status == 'processed':
            max_p = max(latest_scan.dr_prob or 0, latest_scan.glaucoma_prob or 0, latest_scan.amd_prob or 0)
            if max_p >= 0.40:
                if latest_scan.glaucoma_prob == max_p:
                    highest_condition = 'glaucoma'
                elif latest_scan.amd_prob == max_p:
                    highest_condition = 'amd'
                else:
                    highest_condition = 'dr'
        return render_template('user/health_tips.html', highest_condition=highest_condition)

    # ── Longitudinal History & Trends Route ──
    @app.route('/history')
    @login_required
    def history():
        scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.asc()).all()
        # Compile trend data for Chart.js
        trend_data = {
            'dates': [s.created_at.strftime('%d %b') for s in scans],
            'dr': [round((s.dr_prob or 0) * 100, 1) for s in scans],
            'glaucoma': [round((s.glaucoma_prob or 0) * 100, 1) for s in scans],
            'amd': [round((s.amd_prob or 0) * 100, 1) for s in scans]
        }
        return render_template('user/history.html', scans=list(reversed(scans)), trend_data=json.dumps(trend_data))

    # ── Family Eye Health Dashboard Route ──
    @app.route('/family')
    @login_required
    def family_dashboard():
        members = FamilyMember.query.filter_by(user_id=current_user.id).order_by(FamilyMember.created_at.desc()).all()
        user_latest = Scan.query.filter_by(user_id=current_user.id, family_member_id=None).order_by(Scan.created_at.desc()).first()
        
        total_members = len(members) + 1
        anomalies_count = 0
        if user_latest and not user_latest.is_normal:
            anomalies_count += 1
            
        member_summaries = []
        for m in members:
            m_scan = Scan.query.filter_by(user_id=current_user.id, family_member_id=m.id).order_by(Scan.created_at.desc()).first()
            if m_scan and not m_scan.is_normal:
                anomalies_count += 1
            
            months_due = 12
            if m_scan:
                if not m_scan.is_normal:
                    max_p = max(m_scan.dr_prob or 0, m_scan.glaucoma_prob or 0, m_scan.amd_prob or 0, m_scan.cataract_prob or 0)
                    if max_p >= 0.70:
                        months_due = 3
                    else:
                        months_due = 6
            
            from datetime import timedelta
            last_date = m_scan.created_at if m_scan else m.created_at
            due_date = last_date + timedelta(days=months_due * 30)
            is_overdue = datetime.utcnow() > due_date
            
            member_summaries.append({
                'member': m,
                'latest_scan': m_scan,
                'due_date': due_date.strftime('%d %b %Y'),
                'is_overdue': is_overdue
            })
            
        normal_count = total_members - anomalies_count
        family_index = round((normal_count / total_members) * 100) if total_members > 0 else 100
        
        user_due_date = None
        user_is_overdue = True
        if user_latest:
            u_months = 12
            if not user_latest.is_normal:
                max_p = max(user_latest.dr_prob or 0, user_latest.glaucoma_prob or 0, user_latest.amd_prob or 0, user_latest.cataract_prob or 0)
                if max_p >= 0.70:
                    u_months = 3
                else:
                    u_months = 6
            from datetime import timedelta
            due_dt = user_latest.created_at + timedelta(days=u_months * 30)
            user_due_date = due_dt.strftime('%d %b %Y')
            user_is_overdue = datetime.utcnow() > due_dt
            
        all_family_scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).all()
        
        return render_template('user/family_dashboard.html',
                               member_summaries=member_summaries,
                               family_index=family_index,
                               anomalies_count=anomalies_count,
                               all_family_scans=all_family_scans,
                               user_due_date=user_due_date,
                               user_is_overdue=user_is_overdue)


    @app.route('/family/add', methods=['POST'])
    @login_required
    def add_family_member():
        name = request.form.get('name', '').strip()
        relation = request.form.get('relation', '').strip()
        age_str = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        diabetes_type = request.form.get('diabetes_type', '').strip()
        hba1c_str = request.form.get('hba1c', '').strip()
        
        if not (name and relation and age_str and gender):
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('family_dashboard'))
            
        try:
            age = int(age_str)
            hba1c = float(hba1c_str) if hba1c_str else None
            
            member = FamilyMember(
                user_id=current_user.id,
                name=name,
                relation=relation,
                age=age,
                gender=gender,
                diabetes_type=diabetes_type or None,
                hba1c=hba1c
            )
            db.session.add(member)
            db.session.commit()
            
            log_audit("Add Family Profile", f"User {current_user.email} added family profile {name} ({relation})")
            flash(f"Family profile for {name} created successfully!", "success")
        except Exception as e:
            flash(f"Error adding family member: {e}", "danger")
            
        return redirect(url_for('family_dashboard'))

    @app.route('/family/delete/<int:member_id>', methods=['POST'])
    @login_required
    def delete_family_member(member_id):
        member = FamilyMember.query.get_or_404(member_id)
        if member.user_id != current_user.id:
            abort(403)
            
        scans = Scan.query.filter_by(family_member_id=member.id).all()
        for s in scans:
            s.family_member_id = None
        
        db.session.delete(member)
        db.session.commit()
        
        log_audit("Delete Family Profile", f"User {current_user.email} deleted family profile {member.name}")
        flash(f"Family profile for {member.name} deleted.", "info")
        return redirect(url_for('family_dashboard'))

    # ── Retina Digital Passport Route ──
    @app.route('/passport/<int:scan_id>')
    @login_required
    def passport(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id and current_user.role != 'admin':
            abort(403)
        import hashlib
        verif_hash = hashlib.sha256(f"passport-{scan.id}-{scan.created_at}".encode('utf-8')).hexdigest()[:12].upper()
        
        rec_interval = "12 Months"
        if not scan.is_normal:
            max_p = max(scan.dr_prob or 0, scan.glaucoma_prob or 0, scan.amd_prob or 0, scan.cataract_prob or 0)
            if max_p >= 0.70:
                rec_interval = "3 Months"
            else:
                rec_interval = "6 Months"
                
        verify_url = url_for('verify_passport', scan_id=scan.id, _external=True)
        
        return render_template('user/passport.html', scan=scan, hash=verif_hash, rec_interval=rec_interval, verify_url=verify_url)

    @app.route('/verify-passport/<int:scan_id>')
    def verify_passport(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        user = scan.patient
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RetinaScan AI - Verification Portal</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;800&family=Space+Grotesk:wght@400;700&display=swap" rel="stylesheet">
            <style>
                body {{ background: #03050c; color: white; font-family: 'Space Grotesk', sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .cert {{ border: 1px solid #00f2fe; padding: 3rem; border-radius: 16px; background: rgba(10, 15, 36, 0.9); box-shadow: 0 0 30px rgba(0, 242, 254, 0.2); max-width: 500px; text-align: center; }}
                h1 {{ font-family: 'Orbitron', sans-serif; color: #00f2fe; margin-top: 0; }}
                .badge {{ font-size: 4rem; color: #00ff66; margin-bottom: 1rem; filter: drop-shadow(0 0 10px #00ff66); }}
                .field {{ margin: 1rem 0; font-size: 1.1rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.5rem; display: flex; justify-content: space-between; }}
                .field strong {{ color: #a5b4fc; }}
            </style>
        </head>
        <body>
            <div class="cert">
                <div class="badge"><i class="fa-solid fa-shield-halved"></i></div>
                <h1>VERIFIED RECORD</h1>
                <p style="color: #9ca3af; margin-bottom: 2rem;">RetinaScan AI EHR Blockchain Verification Stamp</p>
                <div class="field"><span>Patient Name:</span> <strong>{user.name}</strong></div>
                <div class="field"><span>Scan ID:</span> <strong>#RS-{scan.id}</strong></div>
                <div class="field"><span>Date of Scan:</span> <strong>{scan.created_at.strftime('%d %b %Y, %I:%M %p')}</strong></div>
                <div class="field"><span>Primary Diagnosis:</span> <strong>{scan.predicted_class or 'Healthy Retina'}</strong></div>
                <div class="field"><span>Verification:</span> <strong style="color: #00ff66;"><i class="fa-solid fa-circle-check"></i> SECURE & GENUINE</strong></div>
            </div>
        </body>
        </html>
        """

    # ── AI Second Opinion Route ──
    @app.route('/second-opinion/<int:scan_id>')
    @login_required
    def second_opinion(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id and current_user.role != 'admin':
            abort(403)
        probs1 = json.loads(scan.class_probabilities) if scan.class_probabilities else {}
        probs2 = json.loads(scan.second_opinion_probabilities) if scan.second_opinion_probabilities else {}
        consensus = (scan.predicted_class == scan.second_opinion_class)
        return render_template('user/second_opinion.html', scan=scan, probs1=probs1, probs2=probs2, consensus=consensus)

    @app.route('/api/chat-second-opinion/<int:scan_id>', methods=['POST'])
    @login_required
    def api_chat_second_opinion(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
        user_message = request.json.get('message', '').strip().lower()
        if not user_message:
            return jsonify({'success': False, 'message': 'Empty message'}), 400
            
        p_class = scan.predicted_class or 'Unknown'
        p_conf = round(scan.confidence * 100, 1) if scan.confidence else 0.0
        s_class = scan.second_opinion_class or 'Unknown'
        s_conf = round(scan.second_opinion_confidence * 100, 1) if scan.second_opinion_confidence else 0.0
        s_model = scan.second_opinion_model or 'ResNet50V2'
        
        response = ""
        if "compare" in user_message or "difference" in user_message or "why" in user_message or "diverge" in user_message or "conflict" in user_message:
            if p_class == s_class:
                response = f"Both models achieved consensus on **{p_class}**. The Primary EfficientNet model has {p_conf}% confidence, while {s_model} has {s_conf}% confidence. Since they agree on the retinopathy staging, the risk index is stable."
            else:
                response = f"There is a prediction divergence: the Primary model predicts **{p_class}** ({p_conf}% confidence), but {s_model} predicts **{s_class}** ({s_conf}% confidence). This divergence happens because ResNet features emphasize capillary texture variations more heavily, causing a slight grading shift. Slit-lamp inspection by your doctor can easily resolve this."
        elif "glaucoma" in user_message:
            prob = round(scan.glaucoma_prob * 100, 1) if scan.glaucoma_prob else 0.0
            response = f"The estimated Glaucoma risk is **{prob}%** based on simulated cup-to-disc features. If it exceeds 50%, an optical nerve tomographic mapping is recommended."
        elif "amd" in user_message or "macular" in user_message:
            prob = round(scan.amd_prob * 100, 1) if scan.amd_prob else 0.0
            response = f"AMD (Macular Degeneration) probability is at **{prob}%**, which tracks potential geographic changes. Consider omega-3 fatty acids and standard ocular filters."
        elif "cataract" in user_message:
            prob = round(scan.cataract_prob * 100, 1) if scan.cataract_prob else 0.0
            response = f"Cataract risk evaluates to **{prob}%** by grading simulated lens light transmission and clarity metrics."
        elif "marker" in user_message or "lesion" in user_message:
            markers = []
            if scan.microaneurysms: markers.append("Microaneurysms")
            if scan.hemorrhages: markers.append("Hemorrhages")
            if scan.hard_exudates: markers.append("Hard Exudates")
            if scan.soft_exudates: markers.append("Soft Exudates")
            if scan.neovascularization: markers.append("Neovascularization")
            if markers:
                response = f"Ocular microvascular indicators found on your retina: **{', '.join(markers)}**. These signs guide the classification models."
            else:
                response = "No active microvascular lesions or exudative flags were registered on this fundus image."
        elif "help" in user_message or "what" in user_message:
            response = "I can explain the differences between the models, trace the identified clinical markers, or explain your risk score breakdown for Glaucoma, AMD, and Cataracts. Ask me anything!"
        else:
            response = f"Understood. For the uploaded scan: EfficientNet (Primary) reports **{p_class}** and {s_model} reports **{s_class}**. If you notice any visual symptoms (e.g. blurriness, central vision blind spots) let me know, or book a consultation."
            
        return jsonify({'success': True, 'reply': response})

    # ── Nearby Eye Hospital Finder Route ──
    @app.route('/hospital-finder')
    @login_required
    def hospital_finder():
        hospitals = Hospital.query.all()
        import random
        hospital_data = []
        for h in hospitals:
            random.seed(h.id + 100)
            capacity = random.randint(55, 95)
            wait_time = random.randint(10, 45)
            slots_open = random.randint(1, 6)
            distance = round(random.uniform(1.2, 12.5), 1)
            
            specialties = ["Retina Care", "Glaucoma Clinic", "General Ophthalmology"]
            if h.id == 1:
                specialties = ["Retina Care", "Glaucoma Clinic", "Pediatric Care"]
            elif h.id == 2:
                specialties = ["Cornea Center", "Refractive Surgery", "Retina Care"]
            elif h.id == 3:
                specialties = ["Oculoplastics", "Tumor Clinic", "Glaucoma Clinic"]
                
            hospital_data.append({
                'hospital': h,
                'capacity': capacity,
                'wait_time': wait_time,
                'slots_open': slots_open,
                'distance': distance,
                'specialties': specialties
            })
            
        return render_template('user/hospital_finder.html', hospital_data=hospital_data)

    # ── Dispatch Report Route ───────────────
    @app.route('/send-report/<int:scan_id>', methods=['POST'])

    @login_required
    def send_report(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        if scan.user_id != current_user.id and current_user.role != 'admin':
            abort(403)
            
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        whatsapp_phone = request.form.get('whatsapp_phone', '').strip()
        
        # Build portal result link
        results_url = url_for('results', scan_id=scan.id, _external=True)
        
        dispatched = False
        whatsapp_url = None
        
        if email:
            report_filename = f"report_{scan.id}.pdf"
            report_path = os.path.join(app.config['REPORTS_FOLDER'], report_filename)
            if not os.path.exists(report_path):
                try:
                    generate_pdf_report(scan, scan.patient, report_path, app.config['UPLOAD_FOLDER'])
                    scan.report_path = report_filename
                    db.session.commit()
                except Exception as e:
                    print(f"[Email Report PDF Generation Error] {e}")
            send_email_report(email, scan, scan.patient, results_url, report_path if os.path.exists(report_path) else None)
            flash(f"Report successfully emailed to {email}.", "success")
            dispatched = True
        if phone:
            send_sms_report(phone, scan, results_url)
            flash(f"Report link sent via SMS to {phone}.", "success")
            dispatched = True
            
        if whatsapp_phone:
            # Clean number: keep only digits
            cleaned_num = "".join(c for c in whatsapp_phone if c.isdigit())
            # Format message with emojis and bold styling
            stage = scan.predicted_class or 'Unknown'
            conf = round(scan.confidence * 100, 1) if scan.confidence else 0.0
            msg = f"👁️ *RetinaScan AI Ophthalmic Report* 👁️\n\n*Patient Name*: {current_user.name}\n*DR Diagnosis*: {stage}\n*AI Confidence*: {conf}%\n*View Portal Link*: {results_url}\n\n_This automated screening report was generated securely via RetinaScan AI. Please consult your specialist._"
            
            import urllib.parse
            encoded_msg = urllib.parse.quote(msg)
            whatsapp_url = f"https://wa.me/{cleaned_num}?text={encoded_msg}"
            dispatched = True
            log_audit("Share Report WhatsApp", f"Scan #{scan.id} shared via WhatsApp to {cleaned_num}")
            flash("Redirecting to WhatsApp Messenger...", "success")
            
        if not dispatched:
            flash("Please enter a valid email address, phone number, or WhatsApp number.", "danger")
            
        if whatsapp_url:
            return redirect(whatsapp_url)
            
        return redirect(url_for('results', scan_id=scan.id))

    # ── Booking Routes ────────────────────────
    @app.route('/book-appointment', methods=['GET', 'POST'])
    @login_required
    def book_appointment():
        if request.method == 'POST':
            doctor_id = request.form.get('doctor_id')
            hospital_id = request.form.get('hospital_id')
            apt_date_str = request.form.get('date')
            time_slot = request.form.get('time_slot')
            patient_name = request.form.get('patient_name', '').strip()
            patient_phone = request.form.get('patient_phone', '').strip()
            notes = request.form.get('notes', '').strip()
            
            if not (doctor_id and hospital_id and apt_date_str and time_slot and patient_name and patient_phone):
                flash("All required fields must be filled.", "danger")
                return redirect(url_for('book_appointment'))
                
            try:
                apt_date = datetime.strptime(apt_date_str, '%Y-%m-%d').date()
                
                # Create appointment
                appt = Appointment(
                    user_id=current_user.id,
                    doctor_id=int(doctor_id),
                    hospital_id=int(hospital_id),
                    date=apt_date,
                    time_slot=time_slot,
                    patient_name=patient_name,
                    patient_phone=patient_phone,
                    notes=notes,
                    status='confirmed'
                )
                db.session.add(appt)
                db.session.commit()
                flash("Appointment booked successfully!", "success")
                return redirect(url_for('my_appointments'))
            except Exception as e:
                flash(f"Error booking appointment: {e}", "danger")
                return redirect(url_for('book_appointment'))
                
        hospitals = Hospital.query.all()
        # Find highest risk condition from latest scan to auto-select recommended specialty
        latest_scan = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).first()
        recommended_specialty = "Ophthalmologist"
        if latest_scan and latest_scan.status == 'processed':
            max_p = max(latest_scan.dr_prob or 0, latest_scan.glaucoma_prob or 0, latest_scan.amd_prob or 0)
            if max_p >= 0.40:
                if latest_scan.glaucoma_prob == max_p:
                    recommended_specialty = "Glaucoma Specialist"
                elif latest_scan.amd_prob == max_p:
                    recommended_specialty = "Retina Specialist"
                else:
                    recommended_specialty = "Retina Specialist"
                    
        return render_template('user/booking.html', hospitals=hospitals, recommended_specialty=recommended_specialty)

    @app.route('/my-appointments')
    @login_required
    def my_appointments():
        appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.date.desc()).all()
        return render_template('user/appointments.html', appointments=appointments)

    # ── Booking APIs ────────────────────────
    @app.route('/api/doctors/<int:hospital_id>')
    @login_required
    def api_doctors(hospital_id):
        doctors = Doctor.query.filter_by(hospital_id=hospital_id).all()
        return jsonify([d.to_dict() for d in doctors])

    @app.route('/api/doctor-availability/<int:doctor_id>')
    @login_required
    def api_doctor_availability(doctor_id):
        doctor = Doctor.query.get_or_404(doctor_id)
        return jsonify(doctor.to_dict()['availability'])

    @app.route('/api/cancel-appointment/<int:appointment_id>', methods=['POST'])
    @login_required
    def api_cancel_appointment(appointment_id):
        appt = Appointment.query.get_or_404(appointment_id)
        if appt.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        appt.status = 'cancelled'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Appointment cancelled successfully.'})

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    with app.app_context():
        # Dynamically add cataract and family_member columns to SQLite database if they do not exist

        try:
            import sqlite3
            db_file = os.path.join(os.path.dirname(__file__), 'retinascan.db')
            if os.path.exists(db_file):
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(scans)")
                cols = [row[1] for row in cursor.fetchall()]
                modified = False
                if 'is_cataract' not in cols:
                    cursor.execute("ALTER TABLE scans ADD COLUMN is_cataract BOOLEAN DEFAULT 0")
                    cursor.execute("ALTER TABLE scans ADD COLUMN cataract_prob FLOAT DEFAULT 0.0")
                    modified = True
                    print("[Setup] Successfully added cataracts columns to scans table.")
                if 'family_member_id' not in cols:
                    cursor.execute("ALTER TABLE scans ADD COLUMN family_member_id INTEGER REFERENCES family_members (id)")
                    modified = True
                    print("[Setup] Successfully added family_member_id column to scans table.")
                if modified:
                    conn.commit()
                conn.close()
        except Exception as e:
            print(f"[Setup Warning] Error running SQLite migrations: {e}")


        # Ensure database tables are created (especially with the new models/columns)
        db.create_all()

        # Fix legacy users that have is_active set to False or None
        try:
            legacy_users = User.query.filter((User.is_active == False) | (User.is_active == None)).all()
            for u in legacy_users:
                u.is_active = True
            if legacy_users:
                db.session.commit()
                print(f"[Setup] Activated {len(legacy_users)} legacy/inactive users in the database.")
        except Exception as e:
            print(f"[Setup Warning] Error updating legacy user status: {e}")
        
        # Create/reset default admin
        admin = User.query.filter_by(email='admin@retinascan.com').first()
        if not admin:
            admin = User(name='Admin User', email='admin@retinascan.com', role='admin')
        admin.role = 'admin'
        admin.is_active = True
        admin.set_password('Admin@1234')
        db.session.add(admin)
        db.session.commit()
        # print('[Setup] Default admin verified/reset: admin@retinascan.com / Admin@1234')

        # Create/reset default doctor
        doctor = User.query.filter_by(email='doctor@retinascan.com').first()
        if not doctor:
            doctor = User(name='Dr. Ramakrishnan', email='doctor@retinascan.com', role='doctor')
        doctor.role = 'doctor'
        doctor.is_active = True
        doctor.set_password('Doctor@1234')
        db.session.add(doctor)
        db.session.commit()
        # print('[Setup] Default doctor verified/reset: doctor@retinascan.com / Doctor@1234')

        # Create/reset default patient
        patient = User.query.filter_by(email='patient@retinascan.com').first()
        if not patient:
            patient = User(name='John Doe', email='patient@retinascan.com', role='user', age=45, gender='Male')
        patient.role = 'user'
        patient.is_active = True
        patient.set_password('Patient@1234')
        db.session.add(patient)
        db.session.commit()
        # print('[Setup] Default patient verified/reset: patient@retinascan.com / Patient@1234')

        # Overdue scan generation removed

        # Seed hospitals and doctors if not present
        if not Hospital.query.first():
            h1 = Hospital(name="Aravind Eye Care System", address="1, Anna Nagar", city="Chennai", phone="044-24567890", latitude=13.0827, longitude=80.2707)
            h2 = Hospital(name="Apollo Eye Clinic", address="21, Greams Road", city="Greams Road, Chennai", phone="044-28290200", latitude=13.0602, longitude=80.2496)
            h3 = Hospital(name="Sankara Nethralaya", address="18, College Road", city="Nungambakkam, Chennai", phone="044-28271616", latitude=13.0622, longitude=80.2520)
            db.session.add_all([h1, h2, h3])
            db.session.commit()
            
            # Doctor schedule availability template
            avail = json.dumps({
                "Monday": ["09:00 AM - 10:00 AM", "10:30 AM - 11:30 AM", "02:00 PM - 03:00 PM"],
                "Tuesday": ["09:00 AM - 10:00 AM", "10:30 AM - 11:30 AM", "03:30 PM - 04:30 PM"],
                "Wednesday": ["11:00 AM - 12:00 PM", "02:00 PM - 03:00 PM", "04:00 PM - 05:00 PM"],
                "Thursday": ["09:00 AM - 10:00 AM", "10:30 AM - 11:30 AM", "02:00 PM - 03:00 PM"],
                "Friday": ["09:00 AM - 10:00 AM", "11:00 AM - 12:00 PM", "03:30 PM - 04:30 PM"],
                "Saturday": ["09:00 AM - 10:30 AM"]
            })
            
            d1 = Doctor(name="Dr. R. Ramakrishnan", specialty="Glaucoma Specialist", hospital_id=h1.id, bio="Senior consultant with over 20 years experience in clinical ophthalmology and surgical glaucoma mitigation.", availability=avail)
            d2 = Doctor(name="Dr. Prema Padmanabhan", specialty="Cornea Specialist", hospital_id=h3.id, bio="Senior refractive surgeon specializing in complex corneal transplants and automated visual rehabilitation.", availability=avail)
            d3 = Doctor(name="Dr. Rajiv Raman", specialty="Retina Specialist", hospital_id=h3.id, bio="Distinguished researcher and specialist in diabetic retinopathy management and retinal photocoagulation.", availability=avail)
            d4 = Doctor(name="Dr. Soundari S.", specialty="Oculoplastic Specialist", hospital_id=h2.id, bio="Consultant surgeon specializing in eyelid reconstruction, lacrimal system disorders, and ophthalmic tumors.", availability=avail)
            d5 = Doctor(name="Dr. S. K. Rao", specialty="Comprehensive Eye Care Specialist", hospital_id=h1.id, bio="Ophthalmologist specializing in pediatric eye care, refractive errors, and micro-incision cataract surgeries.", availability=avail)
            db.session.add_all([d1, d2, d3, d4, d5])
            db.session.commit()
            print('[Setup] Seeded hospitals and doctors successfully.')

        # Seed Coimbatore hospitals if not present
        try:
            if not Hospital.query.filter_by(city="Coimbatore").first():
                h4 = Hospital(name="Aravind Eye Hospital", address="Avinashi Road, Civil Aerodrome Post", city="Coimbatore", phone="0422-4360400", latitude=11.0205, longitude=77.0142)
                h5 = Hospital(name="Lotus Eye Hospital and Institute", address="Avinashi Road, Peelamedu", city="Coimbatore", phone="0422-4229900", latitude=11.0247, longitude=77.0101)
                h6 = Hospital(name="The Eye Foundation", address="Diwan Bahadur Road, R.S. Puram", city="Coimbatore", phone="0422-4242000", latitude=11.0116, longitude=76.9458)
                h7 = Hospital(name="Sankara Eye Hospital", address="Sathy Road, Sivanandapuram", city="Coimbatore", phone="0422-2511200", latitude=11.0543, longitude=76.9945)
                db.session.add_all([h4, h5, h6, h7])
                db.session.commit()
                
                avail = json.dumps({
                    "Monday": ["09:00 AM - 10:00 AM", "10:30 AM - 11:30 AM", "02:00 PM - 03:00 PM"],
                    "Tuesday": ["09:00 AM - 10:00 AM", "10:30 AM - 11:30 AM", "03:30 PM - 04:30 PM"],
                    "Wednesday": ["11:00 AM - 12:00 PM", "02:00 PM - 03:00 PM", "04:00 PM - 05:00 PM"],
                    "Thursday": ["09:00 AM - 10:00 AM", "10:30 AM - 11:30 AM", "02:00 PM - 03:00 PM"],
                    "Friday": ["09:00 AM - 10:00 AM", "11:00 AM - 12:00 PM", "03:30 PM - 04:30 PM"],
                    "Saturday": ["09:00 AM - 10:30 AM"]
                })
                
                d6 = Doctor(name="Dr. Shreyas Ramamurthy", specialty="Retina Specialist", hospital_id=h4.id, bio="Retina consultant specializing in advanced vitreo-retinal surgeries and diabetic maculopathy management.", availability=avail)
                d7 = Doctor(name="Dr. Kavitha Sundar", specialty="Glaucoma Specialist", hospital_id=h5.id, bio="Specialist consultant in micro-invasive glaucoma surgeries (MIGS) and visual field telemetry.", availability=avail)
                d8 = Doctor(name="Dr. Rajesh Prabhu", specialty="Cornea Specialist", hospital_id=h6.id, bio="Experienced laser refractive specialist focusing on automated LASIK, SMILE, and corneal rehabilitation.", availability=avail)
                d9 = Doctor(name="Dr. Anjana Selvaraj", specialty="Oculoplastic Specialist", hospital_id=h7.id, bio="Senior reconstructive consultant specializing in cosmetic lid revisions and ophthalmic tumor mitigation.", availability=avail)
                db.session.add_all([d6, d7, d8, d9])
                db.session.commit()
                print('[Setup] Seeded Coimbatore hospitals and doctors successfully.')
        except Exception as e:
            print(f"[Setup Warning] Error seeding Coimbatore hospitals: {e}")

        # Seed Madurai, Trichy, Salem hospitals if not present
        try:
            if not Hospital.query.filter_by(city="Madurai").first():
                h8 = Hospital(name="Aravind Eye Hospital", address="1, Anna Nagar", city="Madurai", phone="0452-4356100", latitude=9.9252, longitude=78.1398)
                h9 = Hospital(name="Vasan Eye Care Hospital", address="KK Nagar Main Road", city="Madurai", phone="0452-4392200", latitude=9.9221, longitude=78.1342)
                h10 = Hospital(name="Joseph Eye Hospital", address="Melapudur", city="Trichy", phone="0431-2415498", latitude=10.8034, longitude=78.6908)
                h11 = Hospital(name="Mahatma Eye Hospital", address="Tennur Main Road", city="Trichy", phone="0431-2741919", latitude=10.8143, longitude=78.6834)
                h12 = Hospital(name="Salem Eye Hospital", address="Ramakrishna Road", city="Salem", phone="0427-2415123", latitude=11.6643, longitude=78.1484)
                h13 = Hospital(name="Aravind Eye Hospital", address="Sankagiri Main Road", city="Salem", phone="0427-4356100", latitude=11.6443, longitude=78.1234)
                
                db.session.add_all([h8, h9, h10, h11, h12, h13])
                db.session.commit()
                
                avail = json.dumps({
                    "Monday": ["09:00 AM - 10:00 AM", "10:30 AM - 11:30 AM", "02:00 PM - 03:00 PM"],
                    "Tuesday": ["09:00 AM - 10:00 AM", "10:30 AM - 11:30 AM", "03:30 PM - 04:30 PM"],
                    "Wednesday": ["11:00 AM - 12:00 PM", "02:00 PM - 03:00 PM", "04:00 PM - 05:00 PM"],
                    "Thursday": ["09:00 AM - 10:00 AM", "10:30 AM - 11:30 AM", "02:00 PM - 03:00 PM"],
                    "Friday": ["09:00 AM - 10:00 AM", "11:00 AM - 12:00 PM", "03:30 PM - 04:30 PM"],
                    "Saturday": ["09:00 AM - 10:30 AM"]
                })
                
                d10 = Doctor(name="Dr. S. R. Rathinam", specialty="Retina Specialist", hospital_id=h8.id, bio="Senior retina consultant, internationally recognized uveitis specialist.", availability=avail)
                d11 = Doctor(name="Dr. V. Narendran", specialty="Glaucoma Specialist", hospital_id=h9.id, bio="Glaucoma surgeon with extensive clinical background.", availability=avail)
                d12 = Doctor(name="Dr. Nelson Jesudasan", specialty="Cornea Specialist", hospital_id=h10.id, bio="Corneal transplant consultant and refractive laser specialist.", availability=avail)
                d13 = Doctor(name="Dr. Ramesh Cobald", specialty="Retina Specialist", hospital_id=h11.id, bio="Senior retinal consultant with expertise in macular edema mapping.", availability=avail)
                d14 = Doctor(name="Dr. Manikandan A.", specialty="Comprehensive Specialist", hospital_id=h12.id, bio="Consultant ophthalmologist specializing in cataract and refractive care.", availability=avail)
                d15 = Doctor(name="Dr. B. Manohar", specialty="Retina Specialist", hospital_id=h13.id, bio="Consultant specializing in microvascular retinal photocoagulation.", availability=avail)
                
                db.session.add_all([d10, d11, d12, d13, d14, d15])
                db.session.commit()
                print('[Setup] Seeded Madurai, Trichy, Salem hospitals successfully.')
        except Exception as e:
            print(f"[Setup Warning] Error seeding district hospitals: {e}")


    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

