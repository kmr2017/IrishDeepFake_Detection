from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import torch
import ffmpeg
from transformers import pipeline
import librosa
import soundfile as sf
import cv2
from PIL import Image
from transformers import AutoImageProcessor, SiglipForImageClassification
import io
from jiwer import wer

app = Flask(__name__)

# Load pre-trained model for audio deepfake detection
audio_model = pipeline("audio-classification", model="mo-thecreator/Deepfake-audio-detection")

# Initialize the deepfake model and processor for video frames
model_name = "prithivMLmods/deepfake-detector-model-v1"
model = SiglipForImageClassification.from_pretrained(model_name)
processor = AutoImageProcessor.from_pretrained(model_name)

# Updated label mapping for video detection
id2label = {
    "0": "fake",
    "1": "real"
}

# Path for uploaded videos
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed video extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}  
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit for videos

# Traditional DPI Checks: Allowed file types and size
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_file_size(file_path):
    file_size = os.path.getsize(file_path)
    return file_size <= MAX_FILE_SIZE  # Ensure file size is within limit

# Function to extract audio from video using ffmpeg and return as in-memory file
# Function to extract audio from video using librosa (in-memory)
def extract_audio_from_video(video_file):
    try:
        # Load audio directly from the video file
        audio, sr = librosa.load(video_file, sr=None)  # sr=None to preserve the original sampling rate
        audio_file = io.BytesIO()  # Create an in-memory buffer to store the audio
        sf.write(audio_file, audio, sr, format='WAV')  # Write to the in-memory buffer
        audio_file.seek(0)  # Reset pointer to the beginning
        return audio_file, sr
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None, None

# Function to classify the audio for deepfake detection using Hugging Face pipeline
def detect_audio_for_deepfake(audio_file):
    try:
        # Perform classification using Hugging Face's pipeline for deepfake audio detection
        result = audio_model(audio_file)

        # Output the result
        print(f"Predicted label: {result[0]['label']}, with confidence: {result[0]['score']}")
        
        # If the label is "fake", classify it as fake
        if result[0]['label'] == "fake" and result[0]['score'] > 0.8:
            return "Fake"  # Fake audio
        return "Real"  # Real audio
        
    except Exception as e:
        print(f"Error detecting audio deepfake: {e}")
        return False

# Function to classify image (video frame) for deepfake detection
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

        # Perform deepfake detection on the frame
        result = classify_image(img_bytes)
        if 'fake' in result:
            return "Fake"
        results.append(result)

    cap.release()  # Release video capture object
    return "Real" if results else "No frames to process."

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(video_path)

        # Step 1: Extract audio from video without saving (using librosa in-memory)
        audio_file = extract_audio_from_video(video_path)
        if not audio_file:
            return jsonify({"error": "Failed to extract audio from video"}), 500

        # Step 2: Detect deepfakes in both audio and video
        video_fake = process_video(video_path)
        audio_fake = detect_audio_for_deepfake(audio_file)

        # Step 3: If either audio or video is fake, return "Fake"
        
        if "Fake" in video_fake or audio_fake:
            return jsonify({"status": "Fake"}), 200
        else:
            return jsonify({"status": "Real"}), 200

    except Exception as e:
        print(f"Error processing the file: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
