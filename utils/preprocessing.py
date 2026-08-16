import cv2
import numpy as np
from PIL import Image
import os


def preprocess_image(image_path, output_path=None, target_size=(224, 224)):
    """
    Full preprocessing pipeline for retinal fundus images.
    Steps: load → resize → CLAHE → normalize → return array
    """
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot load image: {image_path}")

    # Resize to target size
    img_resized = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)

    # Convert BGR to LAB color space for CLAHE
    lab = cv2.cvtColor(img_resized, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)

    # Apply CLAHE to L channel (contrast limited adaptive histogram equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l_channel)

    # Merge back and convert to RGB
    lab_clahe = cv2.merge([l_clahe, a, b])
    img_preprocessed = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
    img_rgb = cv2.cvtColor(img_preprocessed, cv2.COLOR_BGR2RGB)

    # Save preprocessed image if output path provided
    if output_path:
        cv2.imwrite(output_path, img_preprocessed)

    # Normalize to [0, 1] for model input
    img_array = img_rgb.astype(np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)  # Shape: (1, 224, 224, 3)

    return img_array, img_rgb


def save_preprocessed(img_rgb, output_path):
    """Save the preprocessed RGB image to disk."""
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, img_bgr)


def validate_image(file_path):
    """Check if uploaded file is a valid image."""
    try:
        img = Image.open(file_path)
        img.verify()
        return True
    except Exception:
        return False


def check_image_quality(file_path):
    """
    Check retinal image quality before processing.
    Evaluates:
    - Dimensions (minimum 50x50 px)
    - Blurriness (Laplacian variance, threshold < 15.0)
    - Under/Over exposure (average gray pixel value)
    
    Returns:
      (is_acceptable, issues_list, score)
    """
    issues = []
    img = cv2.imread(file_path)
    if img is None:
        return False, ["Cannot read image file. Ensure it is a valid JPEG/PNG format."], 0.0
    
    h, w, c = img.shape
    if w < 50 or h < 50:
        issues.append(f"Low resolution: {w}x{h}px. Minimum required is 500x500px.")
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Calculate a normalized score for GUI display
    # Assume Laplacian variance of 50.0 is 100% quality, 0.0 is 0% quality
    score = min(1.0, max(0.01, laplacian_var / 50.0))
    
    if laplacian_var < 15.0:
        issues.append(f"Image is too blurry. Sharpness metric is too low ({laplacian_var:.1f}).")
        
    mean_brightness = np.mean(gray)
    if mean_brightness < 20:
        issues.append("Image is too dark (underexposed).")
    elif mean_brightness > 235:
        issues.append("Image is too bright (overexposed).")
        
    is_acceptable = len(issues) == 0
    return is_acceptable, issues, score
