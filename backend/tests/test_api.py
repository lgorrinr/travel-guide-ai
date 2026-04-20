#install pytest
#pip install pytest
#run pytest
#pytest tests/test_api.py

import base64
import json
import pathlib
import sys
import uuid
from datetime import datetime

from chalice.test import Client

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import app as backend_app


class FakeRekognitionClient:
    def detect_text(self, Image):
        _ = Image
        return {
            "TextDetections": [
                {"Type": "LINE", "DetectedText": "Guten Tag!"},
                {"Type": "LINE", "DetectedText": "German in the Afternoon"},
            ]
        }


class FakeTranslateClient:
    def translate_text(self, Text, SourceLanguageCode, TargetLanguageCode):
        _ = SourceLanguageCode
        return {
            "TranslatedText": f"{Text} ({TargetLanguageCode})"
        }


class FakeS3Client:
    def __init__(self):
        self.put_calls = []

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)


class FakeDynamoTable:
    def __init__(self):
        self.items = []

    def put_item(self, Item):
        self.items.append(Item)


class FakeRekognitionNoTextClient:
    def detect_text(self, Image):
        _ = Image
        return {"TextDetections": []}


def test_health_check_returns_ok():
    with Client(backend_app.app) as client:
        response = client.http.get("/")

    assert response.status_code == 200
    payload = response.json_body
    assert payload["success"] is True
    assert payload["data"]["service"] == "travel-guide-backend"


def test_translate_returns_translated_text(monkeypatch):
    monkeypatch.setattr(backend_app, "translate_client", FakeTranslateClient())

    with Client(backend_app.app) as client:
        response = client.http.post(
            "/translate",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"text": "hello world", "target_language": "fr"}),
        )

    assert response.status_code == 200
    payload = response.json_body
    assert payload["success"] is True
    assert payload["data"]["original_text"] == "hello world"
    assert payload["data"]["translated_text"] == "hello world (fr)"
    assert payload["data"]["target_language"] == "fr"


def test_extract_text_rejects_invalid_base64():
    with Client(backend_app.app) as client:
        response = client.http.post(
            "/extract-text",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"image": "invalid"}),
        )

    assert response.status_code == 400
    payload = response.json_body
    assert payload["success"] is False
    assert payload["message"] == 'Field "image" is not valid base64 data.'


def test_process_image_returns_extracted_and_translated_text(monkeypatch):
    fake_table = FakeDynamoTable()
    fake_s3 = FakeS3Client()

    monkeypatch.setattr(backend_app, "rekognition_client", FakeRekognitionClient())
    monkeypatch.setattr(backend_app, "translate_client", FakeTranslateClient())
    monkeypatch.setattr(backend_app, "table", fake_table)
    monkeypatch.setattr(backend_app, "s3_client", fake_s3)

    image_b64 = base64.b64encode(b"fake-image-bytes").decode("utf-8")

    with Client(backend_app.app) as client:
        response = client.http.post(
            "/process-image",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"image": image_b64, "target_language": "es"}),
        )

    assert response.status_code == 200
    payload = response.json_body
    assert payload["success"] is True
    assert payload["data"]["extracted_text"] == "Guten Tag! German in the Afternoon"
    assert payload["data"]["translated_text"] == "Guten Tag! German in the Afternoon (es)"
    assert payload["data"]["target_language"] == "es"


def test_process_image_persists_translation_to_dynamodb(monkeypatch):
    test_bucket_name = "test-bucket"
    fake_table = FakeDynamoTable()
    fake_s3 = FakeS3Client()

    monkeypatch.setattr(backend_app, "rekognition_client", FakeRekognitionClient())
    monkeypatch.setattr(backend_app, "translate_client", FakeTranslateClient())
    monkeypatch.setattr(backend_app, "table", fake_table)
    monkeypatch.setattr(backend_app, "s3_client", fake_s3)
    monkeypatch.setattr(backend_app, "S3_BUCKET", test_bucket_name)

    image_b64 = base64.b64encode(b"fake-image-bytes").decode("utf-8")

    with Client(backend_app.app) as client:
        response = client.http.post(
            "/process-image",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"image": image_b64, "target_language": "de"}),
        )

    assert response.status_code == 200
    assert len(fake_table.items) == 1

    item = fake_table.items[0]
    assert item["original_text"] == "Guten Tag! German in the Afternoon"
    assert item["translated_text"] == "Guten Tag! German in the Afternoon (de)"
    assert item["target_language"] == "de"
    assert item["S3_BUCKET_name"] == test_bucket_name
    uuid.UUID(item["request_id"])
    parsed_timestamp = datetime.fromisoformat(item["timestamp"])
    assert parsed_timestamp.tzinfo is not None
    assert item["image_name"].endswith(".jpg")


def test_process_image_no_text_detected_skips_storage(monkeypatch):
    fake_table = FakeDynamoTable()
    fake_s3 = FakeS3Client()

    monkeypatch.setattr(backend_app, "rekognition_client", FakeRekognitionNoTextClient())
    monkeypatch.setattr(backend_app, "translate_client", FakeTranslateClient())
    monkeypatch.setattr(backend_app, "table", fake_table)
    monkeypatch.setattr(backend_app, "s3_client", fake_s3)

    image_b64 = base64.b64encode(b"fake-image-bytes").decode("utf-8")

    with Client(backend_app.app) as client:
        response = client.http.post(
            "/process-image",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"image": image_b64, "target_language": "es"}),
        )

    assert response.status_code == 200
    payload = response.json_body
    assert payload["success"] is True
    assert payload["message"] == "No text was detected in the image."
    assert payload["data"]["extracted_text"] == ""
    assert payload["data"]["translated_text"] == ""
    assert payload["data"]["target_language"] == "es"
    assert fake_table.items == []
    assert fake_s3.put_calls == []
