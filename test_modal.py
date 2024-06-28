import requests


def query_modal_sadtalker(mp3_url, img_url):

    modal_url = "https://ishaanjav--sadtalker-deployment-run-sadtalker-dev.modal.run"
    payload = {
        "mp3URL": mp3_url,
        "imageURL": img_url
    }

    response = requests.post(modal_url, params=payload)
    return response.json()["sync_url"]


test_mp3 = "https://storage.googleapis.com/storm-user-data/results_7c4b9b68-d03a-4061-aac2-676f6fb9fd96_audios_6.mp3"
test_img = "https://storage.googleapis.com/storm-user-data/buffun.png"
print(query_modal_sadtalker(mp3_url=test_mp3, img_url=test_img))
