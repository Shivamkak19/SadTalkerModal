import requests

url = "https://shivamkak19--sadtalker-deployment-run-sadtalker-dev.modal.run"

# Define the payload
payload = {
    "mp3URL": "https://storage.googleapis.com/storm-user-data/results_7c4b9b68-d03a-4061-aac2-676f6fb9fd96_audios_6.mp3",  # Replace with the actual URL
    "imageURL": "https://storage.googleapis.com/storm-user-data/buffun.png"  # Replace with the actual URL
}

# Send the POST request
response = requests.post(url, params=payload)

# Print the response
print(response.status_code)
print(response.json()) 