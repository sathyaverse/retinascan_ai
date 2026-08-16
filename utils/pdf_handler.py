import os
import re
import json

def parse_pdf_report(pdf_path):
    """
    Reads a PDF file's binary stream, extracts text strings, and scans for clinical keywords.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read()
            # Decode using latin1 to safely handle binary streams and preserve text blocks
            text = content.decode('latin1', errors='ignore')
    except Exception as e:
        print(f"[PDF Parser Error] {e}")
        
    text_lower = text.lower()
    
    # Clinical severity keyword mapping
    predicted_class = "No DR"
    if "proliferative" in text_lower:
        predicted_class = "Proliferative DR"
    elif "severe" in text_lower:
        predicted_class = "Severe DR"
    elif "moderate" in text_lower:
        predicted_class = "Moderate DR"
    elif "mild" in text_lower:
        predicted_class = "Mild DR"
        
    # Check for other eye conditions
    has_glaucoma = "glaucoma" in text_lower
    has_amd = any(x in text_lower for x in ["macular degeneration", "amd", "drusen", "maculopathy"])
    
    # Return structured simulation metrics matching inference outputs
    return {
        'predicted_class': predicted_class,
        'has_glaucoma': has_glaucoma,
        'has_amd': has_amd
    }

def create_pdf_placeholder(upload_folder):
    """
    Creates a beautiful glassmorphic SVG visual placeholder for PDFs if it doesn't exist.
    """
    svg_path = os.path.join(upload_folder, "pdf_placeholder.svg")
    if os.path.exists(svg_path):
        return "pdf_placeholder.svg"
        
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="glass" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2a3042" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#151824" stop-opacity="0.9"/>
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00f2fe"/>
      <stop offset="100%" stop-color="#4facfe"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="20" fill="url(#glass)" stroke="#2b3147" stroke-width="2"/>
  <rect x="50" y="30" width="100" height="140" rx="10" fill="#0f111a" stroke="#252b41" stroke-width="1.5"/>
  <path d="M125 30 L150 55 L150 170 rx=10" fill="none"/>
  <!-- Folded Page Corner -->
  <path d="M130 30 L130 50 L150 50 Z" fill="#252b41"/>
  <!-- File Icon Details -->
  <rect x="65" y="60" width="70" height="6" rx="3" fill="#323a54"/>
  <rect x="65" y="75" width="70" height="6" rx="3" fill="#323a54"/>
  <rect x="65" y="90" width="50" height="6" rx="3" fill="#323a54"/>
  <!-- PDF Badge -->
  <rect x="75" y="115" width="50" height="22" rx="6" fill="url(#accent)"/>
  <text x="100" y="131" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="bold" fill="#0f111a" text-anchor="middle">PDF</text>
  <text x="100" y="182" font-family="system-ui, -apple-system, sans-serif" font-size="9" fill="#8f9bb3" text-anchor="middle">Clinical Eye Report</text>
</svg>"""
    
    try:
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
    except Exception as e:
        print(f"[PDF Placeholder Error] {e}")
        
    return "pdf_placeholder.svg"
