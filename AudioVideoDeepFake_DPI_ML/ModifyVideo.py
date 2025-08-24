import cv2
import numpy as np
import random

def extract_frames(video_path):
    """
    Extract frames from the given video file.
    """
    cap = cv2.VideoCapture(video_path)
    frames = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    
    cap.release()
    return frames

def add_fake_frames_to_real(real_video_path, fake_video_path, output_path, num_fake_frames=5):
    """
    Add random frames from a fake video to random positions in a real video and save the output.
    """
    # Extract frames from both videos
    real_frames = extract_frames(real_video_path)
    fake_frames = extract_frames(fake_video_path)
    
    # Select random fake frames to insert
    random_fake_frames = random.sample(fake_frames, num_fake_frames)
    
    # Initialize video writer for the output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for saving video
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (real_frames[0].shape[1], real_frames[0].shape[0]))
    
    # Create a new video by inserting fake frames into the real video
    modified_video_frames = []
    fake_frame_indices = random.sample(range(len(real_frames) + num_fake_frames), num_fake_frames)
    
    real_frame_index = 0
    fake_frame_index = 0
    
    # Insert random fake frames into the real video
    for i in range(len(real_frames) + num_fake_frames):
        if i in fake_frame_indices:
            modified_video_frames.append(random_fake_frames[fake_frame_index])
            fake_frame_index += 1
        else:
            modified_video_frames.append(real_frames[real_frame_index])
            real_frame_index += 1

    # Write modified frames to the output video
    for frame in modified_video_frames:
        out.write(frame)

    # Release the video writer
    out.release()

    print(f"Modified video saved to: {output_path}")

# Example usage
real_video_path = 'real.mp4'  # Path to your real video
fake_video_path = 'fake.mp4'  # Path to your fake video
output_path = 'modified_video.mp4'  # Path where the modified video will be saved

# Call the function to insert fake frames into the real video
add_fake_frames_to_real(real_video_path, fake_video_path, output_path, num_fake_frames=5)
