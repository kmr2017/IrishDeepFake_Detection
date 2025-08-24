import requests

# Server URL where the Flask app is running
server_url = "http://127.0.0.1:5002/upload_video"  # Use your server's URL and port

def upload_file(file_path):
    """
    Function to upload a video file to the server
    """
    with open(file_path, 'rb') as file:
        files = {'file': (file_path, file)}
        response = requests.post(server_url, files=files)
        
        # Check if the response is valid
        if response.status_code == 200:
            print("Server Response:")
            print(response.json())  # This should be the deepfake detection result (real/fake)
        else:
            print("Error uploading file. Server responded with:", response.status_code)

if __name__ == "__main__":
    # File path to the video to be tested (real or fake)
    file_path = "modified_video.mp4"  # Example video file

    print(f"Uploading file: {file_path} to server...")
    upload_file(file_path)
