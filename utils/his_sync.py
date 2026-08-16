import json
import uuid
from datetime import datetime

def sync_scan_to_his(scan, user):
    """
    Simulate syncing a retina scan result to a Hospital Information System (HIS).
    Generates standard clinical integration payloads:
    1. HL7 FHIR (Fast Healthcare Interoperability Resources) DiagnosticReport JSON.
    2. HL7 v2.x ORU^R01 (Observation Result) Message text.

    Args:
        scan: Scan model instance
        user: User model instance

    Returns:
        dict: containing fhir_json (str), hl7_text (str), and fhir_id (str)
    """
    # 1. Generate FHIR DiagnosticReport JSON
    fhir_id = f"diag-rep-{uuid.uuid4().hex[:8]}"
    patient_id = f"pat-{user.id:04d}"
    
    fhir_resource = {
        "resourceType": "DiagnosticReport",
        "id": fhir_id,
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "RAD",
                        "display": "Radiology"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "86807-5",
                    "display": "Diabetic Retinopathy Screening Report"
                }
            ],
            "text": "Retinal Scan AI Automated Screening"
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
            "display": user.name
        },
        "effectiveDateTime": scan.created_at.isoformat() + "Z",
        "issued": datetime.utcnow().isoformat() + "Z",
        "performer": [
            {
                "display": "RetinaScan AI Engine v1.0"
            }
        ],
        "media": [
            {
                "comment": "Original Fundus Photograph",
                "link": {
                    "reference": f"DocumentReference/doc-{scan.id:04d}",
                    "display": scan.original_image
                }
            }
        ],
        "conclusion": f"AI diagnostic screening completed. Primary: {scan.predicted_class} (Confidence: {round((scan.confidence or 0) * 100, 1)}%). Multilabel profile: Glaucoma: {round(scan.glaucoma_prob * 100, 1)}%, AMD: {round(scan.amd_prob * 100, 1)}%.",
        "conclusionCode": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "428341000124108" if scan.predicted_class != 'No DR' else "134385008",
                        "display": f"Diabetic Retinopathy stage - {scan.predicted_class}"
                    }
                ]
            }
        ],
        "extension": [
            {
                "url": "http://retinascan.ai/fhir/StructureDefinition/multilabel-probabilities",
                "valueString": json.dumps({
                    "diabetic_retinopathy": scan.dr_prob,
                    "glaucoma": scan.glaucoma_prob,
                    "macular_degeneration": scan.amd_prob,
                    "normal_healthy": scan.normal_prob
                })
            }
        ]
    }

    # 2. Generate HL7 v2.5.1 ORU^R01 Message
    # Segments: MSH (Header), PID (Patient Id), OBR (Observation Request), OBX (Observation Result)
    msg_time = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    patient_name_hl7 = user.name.replace(' ', '^')
    gender_hl7 = user.gender[0] if user.gender else 'U'
    dob_hl7 = (datetime.utcnow().year - (user.age or 40)) # approximate birth year
    
    hl7_lines = [
        f"MSH|^~\\&|RETINASCAN_AI|AI_PORTAL|HIS_RECEIVER|CLINIC_DB|{msg_time}||ORU^R01^ORU_R01|MSG{scan.id:06d}|P|2.5.1",
        f"PID|1||{patient_id}||{patient_name_hl7}||{dob_hl7}0101|{gender_hl7}|||{user.phone or ''}",
        f"OBR|1||RS-ORDER-{scan.id:05d}|86807-5^Diabetic Retinopathy Screening Report^LN|||{msg_time}|||||||||||||||||F",
        f"OBX|1|ST|DR_STAGE^Diabetic Retinopathy Stage^LN||{scan.predicted_class or 'Unknown'}|||N|||F|||{msg_time}",
        f"OBX|2|NM|DR_PROB^Diabetic Retinopathy Prob^LN||{round(scan.dr_prob, 4)}|%|||N|||F|||{msg_time}",
        f"OBX|3|NM|GLAUCOMA_PROB^Glaucoma Prob^LN||{round(scan.glaucoma_prob, 4)}|%|||N|||F|||{msg_time}",
        f"OBX|4|NM|AMD_PROB^AMD Prob^LN||{round(scan.amd_prob, 4)}|%|||N|||F|||{msg_time}",
        f"OBX|5|TX|CLINICAL_MARKERS^Clinical Markers^LN||MA={scan.microaneurysms};HE={scan.hemorrhages};HE_EX={scan.hard_exudates};SO_EX={scan.soft_exudates};NV={scan.neovascularization}||||||F"
    ]
    hl7_text = "\r".join(hl7_lines)

    # 3. Simulate network delay and response
    print(f"[HIS Sync] Synchronizing Scan #{scan.id} for Patient {user.name} to HIS...")
    print(f"[HIS Sync] Target FHIR Resource ID: DiagnosticReport/{fhir_id}")

    return {
        'fhir_json': json.dumps(fhir_resource, indent=2),
        'hl7_text': hl7_text,
        'fhir_id': fhir_id
    }
