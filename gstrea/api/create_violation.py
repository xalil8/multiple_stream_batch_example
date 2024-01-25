import requests


def create_violation(camera_id, violation_type_id, image_path):
    response = requests.post("http://0.0.0.0:13271/violation/create", json={
        "camera_id": camera_id,
        "violation_type_id": violation_type_id,
        "image_path": image_path
    })
    print(response.json())
    return response.json()