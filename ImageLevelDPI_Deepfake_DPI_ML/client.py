import requests

def upload_file(file_path, server_url="http://127.0.0.1:5001/upload_video"):
    """
    Upload a file to the Flask server for deepfake detection.
    """
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'application/octet-stream')}
        response = requests.post(server_url, files=files)
        return response.json()


file_path = "real.mp4"  
response = upload_file(file_path)
print(response)
