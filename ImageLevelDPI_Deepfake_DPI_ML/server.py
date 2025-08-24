import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import torch
from transformers import AutoImageProcessor, SiglipForImageClassification
import io
import mimetypes
import hashlib
import cv2  # For video processing

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
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}  # Allow only video formats
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit for videos

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

# Load your trained deepfake model
# def classify_image(image_bytes):
#     image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#     inputs = processor(images=image, return_tensors="pt")

#     with torch.no_grad():
#         outputs = model(**inputs)
#         logits = outputs.logits
#         probs = torch.nn.functional.softmax(logits, dim=1).squeeze().tolist()
def classify_image(image_bytes, threshold=0.7):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1).squeeze().tolist()

    # Filter out labels with low probability
    prediction = {
        id2label[str(i)]: round(probs[i], 3) 
        for i in range(len(probs)) 
        if probs[i] > threshold
    }

    return prediction


# Process the video frame-by-frame for deepfake detection
def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return "Error: Could not open video file."

    results = []
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print(f"End of video or failed to read a frame. Total frames processed: {frame_count}")
            break
        
        frame_count += 1

        # Convert the frame to image format (JPEG) for deepfake detection
        _, img_bytes = cv2.imencode('.jpg', frame)
        img_bytes = img_bytes.tobytes()

        # Perform DPI checks on the frame
        if not check_image_signature(img_bytes):
            print(f"Suspicious frame {frame_count} detected. Video is fake.")
            return f"Suspicious frame {frame_count} detected. Video is fake."

        # Perform deepfake detection on the frame
        result = classify_image(img_bytes)
        if 'fake' in result:
            return "No clean content and Video is not allowed"
        results.append(result)

    cap.release()  # Release video capture object
    return "Clean content, video allowed." if results else "No frames to process."

# Flask endpoint to upload video for deepfake detection
@app.route('/upload_video', methods=['POST'])
def upload_video():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        print(f"Uploading file: {file.filename}")

        # Step 1: Read the file content and save it
        file_content = file.read()

        # Step 2: Perform DPI checks (file type and size)
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format'}), 400

        video_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        print(f"Saving video to: {video_path}")
        
        # Step 3: Save the file content to disk
        with open(video_path, 'wb') as f:
            f.write(file_content)

        # Step 4: Perform file size check
        if not check_file_size(video_path):
            return jsonify({'error': 'File size exceeds the limit'}), 400

        # Step 5: Process the video if it passes DPI checks
        video_result = process_video(video_path)
        print(f"Video processing result: {video_result}")
        
        if "Suspicious" in video_result:
            return jsonify({'error': video_result}), 403
        
        return jsonify({'message': video_result}), 200
    
    except Exception as e:
        # Catch any unhandled exception and print it for debugging
        print(f"Error processing the file: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500

# Start the Flask server
if __name__ == '__main__':
    app.run(debug=True, port=5002)
