import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import torch
from transformers import AutoImageProcessor, SiglipForImageClassification
import io
from scapy.all import *  # For DPI simulation

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

# DPI Check: Monitor network traffic for malicious uploads
def check_traffic_anomalies():
    """
    Simulate traffic monitoring: Check for high-frequency uploads or large packets.
    """
    print("Monitoring traffic for abnormal patterns...")

def monitor_protocols():
    """
    Simulate protocol monitoring: Detects unusual protocols (like unusual ports or non-standard usage).
    """
    print("Checking for protocol anomalies...")
    
    # Use Scapy to analyze network packets and detect unusual traffic
    sniff(prn=check_protocol, store=0)  # Monitor packets for protocol anomalies

def check_protocol(packet):
    """
    Check for packets using unusual ports or non-standard protocols.
    """
    allowed_ports = [80, 443, 58121, 58120]  # Add custom ports here
    if packet.haslayer(TCP):
        if packet[TCP].dport not in allowed_ports:  # Check if port is in the allowed list
            print(f"Suspicious protocol detected: {packet.summary()}")

# Flask endpoint to upload image for deepfake detection
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Read file bytes for DPI checks (simulating traffic analysis)
    image_bytes = file.read()

    # Step 1: Perform DPI checks
    # check_traffic_anomalies()  # Custom function to monitor abnormal traffic
    # monitor_protocols()  # Check for unusual protocols used for image uploads

    # Step 2: Perform file size check and allow only legitimate files
    if not allowed_file(file.filename) or not check_file_size(file.filename):
        return jsonify({'error': 'Invalid file format or file size exceeds the limit'}), 400
    
    # Step 3: Perform deepfake detection
    result = classify_image(image_bytes)

    # Return the result of the deepfake detection
    return jsonify(result)

# Start the Flask server
if __name__ == '__main__':
    app.run(debug=True, port=5002)
