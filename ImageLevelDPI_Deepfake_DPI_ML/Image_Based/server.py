import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import torch
from transformers import AutoImageProcessor, SiglipForImageClassification
import io
import mimetypes
import hashlib

# Initialize the deepfake model and processor
model_name = "prithivMLmods/deepfake-detector-model-v1"
model = SiglipForImageClassification.from_pretrained(model_name)
processor = AutoImageProcessor.from_pretrained(model_name)

# Updated label mapping
id2label = {
    "0": "fake",
    "1": "real"
}

# Flask app setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}  # Allow only image formats
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit for images

# Load your trained deepfake model
def classify_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1).squeeze().tolist()

    prediction = {
        id2label[str(i)]: round(probs[i], 3) for i in range(len(probs))
    }

    return prediction

# Traditional DPI Checks: Allowed file types and size
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_file_size(file_path):
    file_size = os.path.getsize(file_path)
    return file_size <= MAX_FILE_SIZE  # Ensure file size is within limit

# Function to check if the image file has a valid signature (magic number)
def check_image_signature(image_bytes):
    # JPEG files start with FF D8 FF E0 or FF D8 FF E1
    # PNG files start with 89 50 4E 47 0D 0A 1A 0A
    # GIF files start with 47 49 46 38 (GIF87a or GIF89a)

    signatures = {
        b'\xFF\xD8\xFF\xE0': 'jpeg',
        b'\xFF\xD8\xFF\xE1': 'jpeg',
        b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A': 'png',
        b'\x47\x49\x46\x38': 'gif'
    }

    for signature, format_name in signatures.items():
        if image_bytes.startswith(signature):
            print(f"File has a valid {format_name} signature.")
            return True

    print("Invalid or unrecognized image signature.")
    return False

# Check MIME type of the uploaded file
def check_mime_type(file_path):
    mime_type, encoding = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('image'):
        print(f"Valid MIME type: {mime_type}")
        return True
    else:
        print(f"Invalid MIME type: {mime_type}")
        return False

# Check image checksum to ensure integrity
def check_file_integrity(file_bytes):
    checksum = hashlib.md5(file_bytes).hexdigest()
    print(f"File checksum: {checksum}")
    # You could verify this checksum against a known valid checksum, if necessary.
    return checksum

# Function to check if the file is an image and doesn't contain hidden malicious data
def check_image_integrity(image_bytes):
    try:
        # Try to open the image using PIL (Pillow)
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Check if the image is not corrupted
        print("Image integrity check passed.")
        return True
    except Exception as e:
        print(f"Image integrity check failed: {e}")
        return False

# Flask endpoint to upload image for deepfake detection
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Read file bytes for DPI checks
    image_bytes = file.read()

    # Step 1: Perform DPI checks (file type, size, signature, MIME, checksum)
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file format'}), 400
    if not check_file_size(file.filename):
        return jsonify({'error': 'File size exceeds the limit'}), 400
    if not check_image_signature(image_bytes):
        return jsonify({'error': 'Invalid image signature'}), 400
    if not check_mime_type(file.filename):
        return jsonify({'error': 'Invalid MIME type'}), 400
    if not check_image_integrity(image_bytes):
        return jsonify({'error': 'Corrupted image'}), 400
    check_file_integrity(image_bytes)  # You can also validate checksum if needed

    # Step 2: Perform deepfake detection
    result = classify_image(image_bytes)

    # Return the result of the deepfake detection
    return jsonify(result)

# Start the Flask server
if __name__ == '__main__':
    app.run(debug=True, port=5003)
