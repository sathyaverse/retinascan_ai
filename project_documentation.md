# RetinaScan AI — Project Documentation

## 1. Abstract

### The Problem Being Addressed
Diabetic Retinopathy (DR) is one of the leading causes of preventable blindness among the working-age population globally. It is a secondary complication of diabetes mellitus that damages the microvascular structure of the retina. If caught in its early stages, vision loss can be successfully mitigated through proper glycemic control and ophthalmic treatment. However, several critical barriers prevent early detection:
- **Scarcity of Specialists**: There is a severe shortage of ophthalmologists and retina specialists, particularly in rural and semi-urban areas, leading to delayed appointments and diagnoses.
- **Asymptotic Early Stages**: Early-stage DR (Mild to Moderate Non-Proliferative Diabetic Retinopathy) often manifests without noticeable visual symptoms, causing patients to postpone screenings until irreversible damage has occurred.
- **Diagnostic Bottlenecks**: Manual assessment of retinal fundus images is time-consuming, highly subjective, and prone to intra- and inter-observer variability.
- **Clinical Integration Gaps**: Traditional screening systems lack seamless integration with hospital databases (HIS/EHR), fail to parse medical standard imaging formats (DICOM) natively, and do not provide automated, explainable reports for patients and general practitioners.

### Proposed Solution
**RetinaScan AI** is an advanced, web-based diagnostic and clinical screening platform powered by deep learning. The platform enables rapid, objective, and explainable screening of retinal fundus photographs. 
Key components of the proposed solution include:
- **CNN Classification Engine**: A custom Convolutional Neural Network (CNN) built on TensorFlow/Keras that classifies retinal images into five distinct severity stages (No DR, Mild DR, Moderate DR, Severe DR, and Proliferative DR) in compliance with the International Clinical Diabetic Retinopathy scale.
- **Explainable AI (XAI)**: Integration of Grad-CAM (Gradient-weighted Class Activation Mapping) which generates activation heatmaps highlighting the exact pathological regions (e.g., hemorrhages, exudates, microaneurysms) that influenced the CNN’s prediction.
- **Multi-Disease Screening**: Parallel multi-label risk assessment for other major retinal pathologies, including Glaucoma, Age-Related Macular Degeneration (AMD), and Cataracts.
- **Interoperability (DICOM & HIS)**: A robust integration layer utilizing PyDicom to extract metadata and image frames directly from standard medical DICOM files, along with support for syncing data to Hospital Information Systems via HL7 FHIR and HL7 v2.x standards.
- **Automated Clinical Reporting**: Rapid generation of patient-centric and clinical PDF reports via ReportLab, containing side-by-side fundus and Grad-CAM images, disease risk charts, clinical marker lists, and tailored medical recommendations.
- **Telemedicine Portal**: A workflow matching patients with ophthalmologists for secondary validation, scheduling, and digital signature sign-offs.

### Expected Outcome
- **Reduced Diagnostic Turnaround**: Retinal screenings can be completed in seconds rather than days, allowing clinics to scale their screening capacity.
- **Increased Diagnostic Accuracy**: By combining a primary deep learning model with an ensemble/second-opinion module (ResNet50V2), screening errors are minimized.
- **Enhanced Clinical Trust**: Explainable Grad-CAM heatmaps prevent the "black box" dilemma, giving clinicians visual evidence to back up AI predictions.
- **Seamless Hospital Workflow**: Instant patient onboarding via DICOM metadata extraction and direct EHR sync via HL7, eliminating manual transcription errors.
- **Broad Accessibility**: Patient-centric design with multilingual translations, automatic email/SMS alerts, and clear, actionable dietary and lifestyle recommendations.

### Objective of the Project
The primary objective of RetinaScan AI is to democratize access to high-quality ophthalmic screenings. By leveraging deep learning and state-of-the-art web technology, the project aims to:
1. Provide a highly accurate, automated utility for early detection of Diabetic Retinopathy and other retinal anomalies.
2. Bridge the gap between engineering and clinical practice by implementing standard medical informatics protocols (DICOM, HL7, FHIR).
3. Deliver a secure, multi-tenant environment (Patients, Doctors, Admins) that manages scans, clinical reviews, and virtual teleconsultations.
4. Improve patient compliance through easy-to-read, downloadable diagnostic summaries and automated appointment reminders.

---

## 2. Existing System

Traditional diabetic retinopathy screening is built around a centralized, manual, and physical referral network. In this framework:
- **Screening Method**: The patient visits a primary care clinic, an optometrist, or an ophthalmology center where a specialized fundus camera captures high-resolution retinal images.
- **Diagnostic Flow**: These images are saved in local folders or sent via traditional email/PACS to a remote retina specialist. The specialist manually reviews each image to identify microaneurysms, hemorrhages, and exudates, assigns a grade, writes notes, and sends the report back to the primary clinic.
- **Integration**: Data transfer between systems relies heavily on manual entry. Demographics are typed out, and files are attached manually, creating significant administrative overhead.

### Drawbacks of the Existing System:
1. **Inefficiency and Delays**: The workflow is highly sequential and dependent on human availability. Patients often wait weeks to receive their diagnostic screening results.
2. **Specialist Overload**: Retina specialists spend valuable clinical hours scanning healthy or mild cases, leaving less time for patients requiring urgent surgical interventions.
3. **High Diagnostic Costs**: The necessity of involving high-level specialists at every stage of baseline screening drives up healthcare expenditures for patients and insurers.
4. **Subjective Variability**: Manual grading is prone to human error, cognitive fatigue, and differences in clinical interpretation, particularly in distinguishing borderline Mild vs. Moderate stages.
5. **Lack of Explainability in Automated Tools**: Existing basic automated screening utilities often provide binary classifications without explaining *why* a decision was made, resulting in low clinician adoption and trust.

---

## 3. Proposed System

The proposed system, **RetinaScan AI**, introduces a secure, automated, and cloud-capable screening ecosystem. It acts as an intelligent assistant to clinical staff, conducting primary triage and automatically highlighting abnormalities.

```mermaid
flowchart TD
    A[Patient / DICOM Upload] --> B[Quality & Validity Check]
    B -->|Passed| C[Contrast Enhancement (CLAHE)]
    B -->|Failed| D[Alert User: Re-upload Image]
    C --> E[AI Diagnostic Core]
    E --> F[CNN Model: DR Stage Classification]
    E --> G[Ensemble Model: Second Opinion]
    E --> H[Multi-Disease Risk Analysis]
    F --> I[Grad-CAM Heatmap Generation]
    F & G & H & I --> J[Database & Audit Logging]
    J --> K[Clinical PDF Report Generation]
    K --> L[Sync to HIS: HL7 FHIR & v2.x Payload]
    K --> M[Email & SMS Dispatch to Patient]
    J --> N[Doctor Review & Digital Signature Sign-off]
```

### Key Improvements in the Proposed System:
- **Automated Screening & Triaging**: Instantly separates normal retinas from those displaying pathological markers, flagging severe cases for immediate attention.
- **Two-Tier Validation (Ensemble)**: Employs a primary CNN model for 5-stage DR classification and a secondary, independent ResNet50V2 model to verify predictions, providing confidence scores for both.
- **Contrast Limited Adaptive Histogram Equalization (CLAHE)**: Retinal photographs often suffer from non-uniform illumination. The preprocessing pipeline applies CLAHE to the Luminance (L) channel of the LAB color space to enhance the visibility of microvascular lesions before feeding them to the AI model.
- **Explainability via Grad-CAM**: Generates a jet-colored visual heatmap showing exactly where the neural network detected pathological signs, increasing clinical accountability.
- **Unified Portal Access**: Provides specific interfaces tailored to three user archetypes:
  1. **Patients**: View history, track diabetic metrics (HbA1c, blood pressure), register family members, schedule appointments, and read wellness/nutritional tips.
  2. **Doctors**: Access an assigned queue of scans, view Grad-CAM heatmaps, write notes, validate classifications, and apply secure digital signatures.
  3. **Administrators**: Manage the user database, audit system logs, review scans, and monitor sync status.
- **Standardized Interoperability**: Natively supports DICOM parser and exports reports in FHIR JSON or HL7 message strings, making it ready for modern hospital deployments.

---

## 4. Hardware Specifications

To support real-time deep learning inference, image preprocessing, and concurrent database reads/writes, the hardware architecture is divided into development/server and client-side systems:

### A. Server / Development System (High-Performance AI Environment)
- **Processor (CPU)**: Intel Core i7 (10th Generation or newer) or AMD Ryzen 7 (3700X or newer) with at least 8 physical cores (16 threads), operating at a base clock speed of 3.6 GHz.
- **Memory (RAM)**: 16 GB DDR4/DDR5 system memory (32 GB recommended for handling high-volume concurrent scans).
- **Graphics Card (GPU - Critical for ML)**: NVIDIA GeForce RTX 3060 / RTX 4060 or better with a minimum of 8 GB VRAM. Support for NVIDIA CUDA Toolkit (v11.8+) and cuDNN is required to accelerate CNN inference times to sub-second levels.
- **Primary Storage**: 512 GB NVMe M.2 SSD for Operating System, application files, and databases to ensure high read/write speeds.
- **Secondary Storage**: 1 TB SATA SSD or HDD for archiving historical high-resolution fundus images, generated PDF reports, and raw DICOM assets.
- **Network Interface**: Gigabit Ethernet (10/100/1000 Mbps) for smooth integration with external Hospital PACS and communication gateways.

### B. Client System (Doctor's Workstation / Clinician Device)
- **Processor**: Intel Core i3 (8th Gen or equivalent) or AMD Ryzen 3.
- **System Memory**: 8 GB RAM.
- **Display**: High-resolution monitor (Full HD 1920x1080) with color calibration to correctly display the retinal fundus images and Grad-CAM color gradients.
- **Input Peripherals**: Standard keyboard, mouse, and option for a digital writing pad (for capturing clinician signatures).

---

## 5. Software Specifications (In Details)

The software architecture is engineered using open-source, robust, and industry-standard technologies to guarantee security, modularity, and high computational performance.

### A. Operating Environment
- **Operating System**: Windows 10/11 64-bit, macOS Monterey (12.0 or newer), or Ubuntu Linux 20.04/22.04 LTS (recommended for production hosting).
- **Runtime Environment**: Python 3.10+ 64-bit.

### B. Backend Technologies & Web Framework
- **Core Framework**: **Flask (v2.3.3)** - A lightweight, WSGI-compliant web application framework used to route HTTP requests, serve static assets, and implement session management.
- **Authentication**: **Flask-Login (v0.6.3)** - Handles user session serialization, cookies, and route protections (`@login_required`).
- **Security & Hashing**: **Flask-Bcrypt (v1.0.1)** - Utilizes the blowfish cipher to securely hash and verify user passwords before database storage.
- **Token Management**: **Flask-JWT-Extended (v4.5.3)** - Facilitates secure JSON Web Token generation for cross-origin API authentication and HIS synchronization routes.
- **Configuration & Environment**: **python-dotenv (v1.0.0)** - Separates database credentials, secrets, and API keys from the source code.

### C. Database Management
- **ORM Interface**: **Flask-SQLAlchemy (v3.1.1)** / **SQLAlchemy (v2.0.21)** - Translates Python models into relational SQL commands, preventing SQL-injection vulnerabilities.
- **Database Engine (Development)**: **SQLite** (file-based database engine, stored locally as `retinascan.db`).
- **Database Engine (Production)**: **MySQL (v8.0)** or **PostgreSQL (v14)** via the `mysqlclient (v2.2.0)` package, providing robust concurrent connection handling, transaction indexing, and security encryption.

### D. Artificial Intelligence & Image Processing Stack
- **Deep Learning Core**: **TensorFlow (v2.13.0)** & **Keras (v2.13.1)** - Used to load the pre-trained Convolutional Neural Network file (`dr_model.h5`), structure the inputs, run predictions, and fetch the final softmax activation probabilities.
- **Explainability**: **tf-keras-vis (v0.8.5)** and **TensorFlow GradientTape** - Intercepts the activations of the final `Conv2D` layer in the model to compute gradients and generate Grad-CAM overlays.
- **Mathematical & Data Analysis**: **Numpy (v1.24.3)** & **Scikit-Learn (v1.3.0)** - Performs efficient matrix normalization, array reshaping, and calculation of metrics.
- **Computer Vision**: **OpenCV-Python (v4.8.1.78)** - Processes fundus photography frames, handles color-space transformations (BGR to LAB, LAB to RGB), applies CLAHE filters, calculates image sharpness/blurriness using Laplacian variance, and handles image overlays.
- **Image Processing Fallback**: **Pillow (v10.0.1)** - Verifies uploaded image headers to prevent malicious payloads disguised as images.
- **DICOM Protocol Handler**: **PyDicom (v2.4.3)** - Reads `.dcm` binary files, extracts medical tags (Patient ID, Name, Age, Sex, Image Laterality), and decodes pixel arrays.

### E. Reporting & Communication
- **PDF Construction Engine**: **ReportLab (v4.0.6)** - Builds pixel-perfect A4 clinical reports dynamically with headers, tables, flowable paragraph structures, and embedded PNG/JPG assets.
- **Visualization Plotting**: **Matplotlib (v3.7.3)** - Used to plot confidence metrics, historical trends, and patient metrics charts.
- **Notification Services**: SMTP standard library (configured for SendGrid/Gmail) for email dispatches, and integration hookups for Twilio SMS APIs.

---

## 6. Module Description

RetinaScan AI is constructed using a modular architecture where each component is isolated, testable, and reusable. The system consists of seven primary modules:

### 1. User Authentication & Profile Module
This module handles onboarding, session control, and demographic details.
- **User Registrations**: Signs up patients, storing email, hashed passwords, and baseline information.
- **Virtual 2-Factor Authentication (2FA)**: When a patient logs in, the system generates a random 6-digit OTP (One-Time Password) with a 5-minute expiration time, simulating secure authentication before routing to the dashboard.
- **Role-Based Access Control (RBAC)**: Segregates views and capabilities. Users are categorized into `user` (patient), `doctor` (ophthalmologist), and `admin` (system manager).
- **Patient Clinical Profile**: Collects and displays demographic variables (Age, Gender) and diabetes history parameters (Diabetes Type, HbA1c history, Diabetes Duration, Systolic/Diastolic blood pressure, and family medical history in JSON format).

### 2. Patient Portal & Family Management Module
Designed to empower patients to track their retinal health and manage care for dependents.
- **Interactive Patient Dashboard**: Displays historical scans with color-coded risk levels and visual charts.
- **Family Member Registration**: Enables primary users to link family members (Dependents) to their account, allowing them to upload and analyze retinal scans for children or elderly relatives who cannot navigate the platform themselves.
- **Appointment Scheduling**: Patients can search for doctors based on specialty, view their hospital affiliations, select available dates/slots, book appointments, and retrieve a virtual queue token number along with a teleconsultation video link.

### 3. Medical Imaging & Preprocessing Module
Responsible for incoming file validation, DICOM parsing, and image enhancement.
- **DICOM Parser**: Detects if an uploaded file has a `.dcm` extension. If so, it utilizes `pydicom` to extract clinical tags (e.g., patient metadata and `ImageLaterality` which indicates if the scan is of the left or right eye). It then converts the underlying pixel matrix into a standard RGB image.
- **Quality & Exposure Assessment**: Performs automated quality checks on the fundus photograph before processing. It rejects images that are too small (resolution check), too dark/bright (mean brightness check), or too blurry (Laplacian variance score).
- **CLAHE Enhancement**: Converts the image into the LAB color space, applies Contrast Limited Adaptive Histogram Equalization to the L-channel to enhance subtle clinical markers, and converts it back to RGB for AI inference.

### 4. AI Inference & Explainability Module
The core ML layer that handles multi-disease classification and pathology visualization.
- **DR Classification**: Loads the primary CNN (`dr_model.h5`), processes the image array (resizing to 224x224 and normalizing to $[0, 1]$), runs a forward pass, and maps outputs to the 5 DR classes.
- **Grad-CAM Generator**: Computes the gradients of the model's prediction score relative to the activation map of the last convolutional layer. It resizes and overlays this heatmap onto the original fundus image to highlight regions of interest (e.g. hard exudates, cotton wool spots).
- **Ensemble Verification (Second Opinion)**: Simulates a second-opinion check using a ResNet50V2 architecture, outputting class comparisons and verification scores.
- **Multi-Disease Profiling**: Evaluates risks for Glaucoma, Cataract, and Macular Degeneration alongside DR, returning a comprehensive retinal health profile.
- **Clinical Marker Extractor**: Translates classification outputs into specific diagnostic markers (e.g., microaneurysms for Mild DR, neovascularization for Proliferative DR) to assist clinical documentation.

### 5. Doctor Portal & Sign-Off Module
An interface designed to assist ophthalmologists with validation and reporting.
- **Case Assignment Queue**: Displays scans uploaded by patients, auto-assigning cases using a load-balancing algorithm that routes new scans to the doctor with the fewest pending tasks.
- **Grad-CAM Interactivity**: Allows doctors to toggle the Grad-CAM heatmap overlay on and off to verify highlighted anomalies.
- **Clinical Sign-Off**: The doctor can review the AI-suggested DR stage, change the class if needed, type clinical notes, and apply a secure digital signature to complete the report.

### 6. Clinical Reporting & HIS Sync Module
Handles interoperability, reporting, and hospital database synchronization.
- **ReportLab PDF Generator**: Compiles metadata, side-by-side images (Fundus and Grad-CAM), disease tables, clinical markers, and recommendations into a professional A4 PDF saved in `/reports`.
- **FHIR Integration**: Generates a standard HL7 FHIR `DiagnosticReport` JSON payload, mapping diagnostic outcomes to SNOMED-CT codes.
- **HL7 v2.x Message Generator**: Synthesizes HL7 v2.5.1 ORU^R01 (Observation Result) text segments (`MSH`, `PID`, `OBR`, `OBX`) for transmission to legacy Hospital Information Systems (HIS) and EHR databases.

### 7. Administration & Audit Logging Module
Ensures system security, auditability, and user management.
- **Admin Dashboard**: Provides global metrics on user registrations, total scans processed, and pending clinical reviews.
- **Audit Logging**: Automatically records every system action (e.g., user registrations, logins, scan uploads, OTP generation, and doctor validations) with timestamps, IP addresses, and descriptions. This maintains an immutable log for security compliance (such as HIPAA).
- **Database Clean-up & Sync Utilities**: Background utilities to clear orphaned records and manage database state.
