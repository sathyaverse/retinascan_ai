# RetinaScan AI — Diabetic Retinopathy Detection Platform

## Project Overview
A web-based diagnostic platform that uses a CNN model to classify retinal fundus images
into 5 DR severity stages with Grad-CAM explainability and automated PDF reporting.

## Tech Stack
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Backend**: Python 3.10+, Flask, Flask-Login, SQLAlchemy
- **AI/ML**: TensorFlow/Keras (dr_model.h5), OpenCV (CLAHE), Grad-CAM
- **Database**: python flask

- **PDF**: ReportLab

## Folder Structure
```
retinascan_ai/
├── app.py                  # Main Flask app with all routes
├── config.py               # Configuration (DB, model path, DR classes)
├── requirements.txt
├── models/
│   ├── __init__.py         # db, bcrypt, login_manager
│   ├── user.py             # User model
│   └── scan.py             # Scan model
├── utils/
│   ├── preprocessing.py    # CLAHE + image normalization
│   ├── inference.py        # CNN model inference
│   ├── gradcam.py          # Grad-CAM heatmap generation
│   └── pdf_report.py       # ReportLab PDF generation
├── templates/
│   ├── base.html           # Master layout (navbar, flash, footer)
│   ├── index.html          # Landing page
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── user/
│   │   ├── dashboard.html
│   │   ├── upload.html
│   │   ├── results.html
│   │   ├── reports.html
│   │   └── profile.html
│   └── admin/
│       ├── dashboard.html
│       ├── users.html
│       └── scans.html
├── static/
│   ├── css/main.css
│   ├── js/
│   │   ├── main.js
│   │   └── upload.js
│   └── uploads/            # Uploaded + processed images
└── reports/                # Generated PDFs
```

## Setup Instructions

### 1. Clone and create virtual environment
```bash
git clone <repo>
cd retinascan_ai
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure MySQL database
Create a database named `retinascan_db` in MySQL, then update `config.py`:
```python
SQLALCHEMY_DATABASE_URI = 'mysql://root:YOUR_PASSWORD@localhost/retinascan_db'
```

### 4. Place your trained model
Copy your trained CNN model file:
```
models/dr_model.h5
```

### 5. Run the application
```bash
python app.py
```
Visit: http://localhost:5000

**Default admin credentials:**
- Email: admin@retinascan.com
- Password: Admin@1234

## DR Severity Classes
| Stage | Description |
|-------|-------------|
| No DR | No retinopathy detected |
| Mild DR | Microaneurysms only |
| Moderate DR | More than microaneurysms |
| Severe DR | Hemorrhages in all 4 quadrants |
| Proliferative DR | Neovascularisation present |

## API Endpoints
| Method | Route | Description |
|--------|-------|-------------|
| GET | / | Landing page |
| GET/POST | /register | User registration |
| GET/POST | /login | Login |
| GET | /logout | Logout |
| GET | /dashboard | User dashboard |
| GET/POST | /upload | Upload retinal image |
| GET | /results/\<id\> | View scan result |
| GET | /reports | My reports list |
| GET | /download-report/\<id\> | Download PDF |
| GET | /profile | User profile |
| GET | /admin | Admin dashboard |
| GET | /admin/users | Manage users |
| GET | /admin/scans | All scans |
| POST | /admin/validate/\<id\> | Validate a scan |
| GET | /api/scan-history | JSON scan history |
