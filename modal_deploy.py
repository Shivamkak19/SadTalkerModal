import modal
from pydantic import BaseModel
import urllib
import uuid
import os
import subprocess
import io
from pydub import AudioSegment
from datetime import timedelta
from credentials import storage_client as storage, firestore_client as db
from dotenv import load_dotenv
import torch

# Load environment variables from .env file
load_dotenv()

PRIVATE_BUCKET_NAME = "storm-user-private"
PUBLIC_BUCKET_NAME = "storm-user-data"
DUMMY_SYNC_MP4 = "https://storage.googleapis.com/storm-user-data/syncs/04e406a0-5444-41d2-851f-51d94e9ccdf7.mp4"

# Define the Docker image from the Dockerfile
docker_image = modal.Image.from_dockerfile("Dockerfile")

# Define the Modal function
app = modal.App("sadtalker-deployment")

class LipSyncRequest(BaseModel):
    mp3URL: str
    imageURL: str

@app.function(image=docker_image, gpu="H100:8")
@modal.web_endpoint(method="POST")
def run_sadtalker(mp3URL: str, imageURL: str):
    print("***", "reached modal")

    # Define the paths to the files and directories
    host_dir = os.getcwd()
    driven_audio = os.path.join(host_dir, "audio_test.wav")
    source_image = os.path.join(host_dir, "image_test.png")
    result_dir = os.path.join(host_dir, "output")

    # Ensure result directory exists
    os.makedirs(result_dir, exist_ok=True)

    print("*** Downloading data")
    # Download and save the image
    image_data = urllib.request.urlopen(imageURL).read()
    with open(source_image, "wb") as f:
        f.write(image_data)

    # Download and save the audio
    audio_data = urllib.request.urlopen(mp3URL).read()
    mp3_audio = io.BytesIO(audio_data)
    print("*** Finished downloading")
    # Load the MP3 audio with pydub
    audio = AudioSegment.from_file(mp3_audio, format="mp3")

    # Export the audio to WAV format
    print("*** Starting export")
    audio.export(driven_audio, format="wav")
    print("*** Finished export")
    with open(driven_audio, "wb") as f:
        f.write(audio_data)

    print("*** Finished converting")

    # Check CUDA availability
    if torch.cuda.is_available():
        print("*** CUDA is available")
    else:
        print("*** CUDA is not available")

    # Construct the command for SadTalker
    sadtalker_command = [
        "python3", "inference.py",
        "--driven_audio", driven_audio,
        "--source_image", source_image,
        "--expression_scale", "1.2",
        "--size", "512",
        "--preprocess", "full",
        "--result_dir", result_dir
    ]

    # Run the SadTalker command
    result = subprocess.run(sadtalker_command, capture_output=True, text=True)
    print("***", result.stdout)
    print("***", result.stderr)
    
    # List the files in the result directory
    result_files = os.listdir(result_dir)
    print("*** Result files:", result_files)
    
    # Upload the generated MP4 file to GCP, delete the local file, and get the signed URLs
    signed_urls = []
    for file_name in result_files:
        if file_name.endswith(".mp4"):
            file_path = os.path.join(result_dir, file_name)

            print("check file path:", file_path)
            unique_path = upload_file_to_gcp(file_path, PUBLIC_BUCKET_NAME)
            os.remove(file_path)
            print(f"Deleted local file: {file_path}")
            signed_url = get_signed_gcp_url(unique_path, PUBLIC_BUCKET_NAME)
            signed_urls.append(signed_url)
    
    if not signed_urls:
        return {"sync_url": DUMMY_SYNC_MP4}
    else:
        return {"sync_url": signed_urls[0]}

def upload_file_to_gcp(file_name, bucket_name):
    print("Uploading file to GCP")
    bucket = storage.bucket(bucket_name)

    unique_path = f"syncs/{uuid.uuid4()}.mp4"
    blob = bucket.blob(unique_path)
    blob.upload_from_filename(file_name)
    print(f"File {file_name} uploaded to {bucket_name}")

    return unique_path

def get_signed_gcp_url(file_name, bucket_name, expiration=timedelta(seconds=3600)):
    print("Getting signed view URL")
    bucket = storage.bucket(bucket_name)
    blob = bucket.blob(file_name)
    return blob.generate_signed_url(expiration, method="GET")

# Entry point to run the Modal function
if __name__ == "__main__":
    with app.run():
        run_sadtalker.call()
