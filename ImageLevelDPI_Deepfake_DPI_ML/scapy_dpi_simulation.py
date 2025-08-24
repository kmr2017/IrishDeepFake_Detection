from scapy.all import *
import time

def send_video_traffic(ip, port, filename, is_fake=False):
    """
    Simulate sending normal (real) or malicious (deepfake) media over the network.
    """
    traffic_type = "fake" if is_fake else "real"
    print(f"Sending {traffic_type} media to {ip}:{port}")

    try:
        # Open the video file and read the content as binary data
        with open(filename, 'rb') as f:
            video_data = f.read()

        # Adjust chunk size to fit within the MTU (typically 1500 bytes for Ethernet)
        chunk_size = 1400  # Larger chunk size (up to 14000 bytes)
        total_chunks = len(video_data) // chunk_size + 1

        # Send the video data in chunks
        for i in range(total_chunks):
            chunk = video_data[i * chunk_size : (i + 1) * chunk_size]

            # Build a Scapy packet
            packet = IP(dst=ip) / TCP(dport=port, sport=RandShort()) / Raw(load=chunk)

            # Send the packet
            send(packet)
            print(f"Sent packet {i+1}/{total_chunks} with chunk size {len(chunk)} bytes.")
            time.sleep(0.1)  # Optional: Add a small delay between packets to simulate realistic traffic

        print(f"Sent {len(video_data)} bytes of {traffic_type} media to {ip}:{port}")

    except Exception as e:
        print(f"Error sending traffic: {e}")

# Example usage:
ip = '127.0.0.1'  # Target IP address (server address)
port = 5001  # Flask server port (make sure it matches your server's port)

# Simulate sending normal media (real)
send_video_traffic(ip, port, 'real.mp4', is_fake=False)

# # Wait for a moment before sending malicious media
# time.sleep(2)

# # Simulate sending deepfake media (malicious)
# send_video_traffic(ip, port, 'fake.mp4', is_fake=True)
