from chalice import Chalice, Response
import base64
import json
import logging
import boto3
import uuid
from datetime import datetime, timezone

# =========================================================
# TRAVEL GUIDE BACKEND
# COMPLETED BY LISSETTE:
# Backend - Chalice + REST API
#
# - Chalice app setup
# - API route structure
# - Input validation
# - Consistent JSON response format
# - Logging
# - Error handling
#
# TO BE COMPLETE BY OTHER TEAM MEMBERS:
# - AWS Rekognition implementation
# - AWS Translate implementation
# - S3/DynamoDB persistence
# - Frontend integration
# - Architecture diagrams
#
# =========================================================

app = Chalice(app_name="travel-guide")
app.log.setLevel(logging.INFO)

rekognition_client = boto3.client("rekognition", region_name="us-east-1")
translate_client = boto3.client("translate", region_name="us-east-1")

# =========================================================
# NOTE FOR MEMBER 4 (Cloud / Data):
# The bucket name S3_BUCKET = "travel-guide-images" is a shared reference only.
# Final S3 setup, permissions, and cloud resource review
# belong to you.
# =========================================================
S3_BUCKET = "travel-guide-images"

s3_client = boto3.client('s3')

dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("TravelGuideTranslations")


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def json_response(status_code: int, success: bool, message: str, data=None):
    """
    Standard JSON response format used by all routes.
    """
    payload = {
        "success": success,
        "message": message,
        "data": data if data is not None else {}
    }

    return Response(
        body=json.dumps(payload),
        status_code=status_code,
        headers={"Content-Type": "application/json"}
    )


def get_json_body():
    """
    Safely return the JSON body from the current request.
    """
    request = app.current_request
    return request.json_body if request else None


def validate_base64_image(body):
    """
    Validate that the request contains a non-empty base64 image string.
    Returns:
        (image_bytes, None) if valid
        (None, error_message) if invalid
    """
    if not body:
        return None, "Request body is missing."

    image_value = body.get("image")

    if image_value is None:
        return None, 'Field "image" is required.'

    if not isinstance(image_value, str) or not image_value.strip():
        return None, 'Field "image" must be a non-empty base64 string.'

    try:
        image_bytes = base64.b64decode(image_value, validate=True)
        return image_bytes, None
    except Exception:
        return None, 'Field "image" is not valid base64 data.'


def validate_text(body):
    """
    Validate that the request contains a non-empty text field.
    """
    if not body:
        return None, "Request body is missing."

    text_value = body.get("text")

    if text_value is None:
        return None, 'Field "text" is required.'

    if not isinstance(text_value, str) or not text_value.strip():
        return None, 'Field "text" must be a non-empty string.'

    return text_value.strip(), None


def validate_target_language(body):
    """
    Validate that the request contains a non-empty target_language field.
    """
    if not body:
        return None, "Request body is missing."

    target_language = body.get("target_language")

    if target_language is None:
        return None, 'Field "target_language" is required.'

    if not isinstance(target_language, str) or not target_language.strip():
        return None, 'Field "target_language" must be a non-empty string.'

    return target_language.strip(), None

def extract_text_lines(image_bytes):
    """
    Detect text lines from an image using Amazon Rekognition.
    """
    response = rekognition_client.detect_text(Image={"Bytes": image_bytes})

    lines = []
    for item in response.get("TextDetections", []):
        if item.get("Type") == "LINE":
            detected = item.get("DetectedText", "").strip()
            if detected:
                lines.append(detected)

    return " ".join(lines).strip()


def translate_content(text_value, target_language):
    """
    Translate text using Amazon Translate.
    """
    response = translate_client.translate_text(
        Text=text_value,
        SourceLanguageCode="auto",
        TargetLanguageCode=target_language
    )

    return response.get("TranslatedText", "").strip()


# =========================================================
# ROUTE 1: HEALTH CHECK
# =========================================================
@app.route("/", methods=["GET"])
def health_check():
    """
    Health check route.
    Used to confirm the backend is running.
    """
    app.log.info("Health check route called.")

    return json_response(
        status_code=200,
        success=True,
        message="Travel Guide API is running.",
        data={
            "service": "travel-guide-backend",
            "owner": "Lissette",
            "available_routes": [
                "GET /",
                "GET /languages",
                "POST /extract-text",
                "POST /translate",
                "POST /process-image"
            ]
        }
    )

# =========================================================
# ROUTE 2: GET SUPPORTED LANGUAGES
#
# NOTE FOR MEMBER 3 (FRONTEND):
# Use this route to dynamically populate the language dropdown.
#
# Response format:
# {
#   "languages": [
#       {"code": "en", "name": "English"},
#       {"code": "fr", "name": "French"}
#   ]
# }
# =========================================================
@app.route("/languages", methods=["GET"], cors=True)
def get_languages():
    try:
        response = translate_client.list_languages(DisplayLanguageCode="en")

        languages = []
        for lang in response.get("Languages", []):
            languages.append({
                "code": lang.get("LanguageCode", ""),
                "name": lang.get("LanguageName", "")
            })

        languages = sorted(languages, key=lambda x: x["name"])

        return json_response(
            status_code=200,
            success=True,
            message="Languages retrieved successfully.",
            data={"languages": languages}
        )

    except Exception as e:
        app.log.exception("Unexpected error in /languages")
        return json_response(
            status_code=500,
            success=False,
            message="Internal server error while processing /languages.",
            data={"details": str(e)}
        )
    
# =========================================================
# ROUTE 3: EXTRACT TEXT
#
# NOTE FOR MEMBER 2 (AI Services):
# Edit ONLY the TODO section inside this function.
# Replace the placeholder with AWS Rekognition text detection.
#
# Expected output in data:
# {
#   "extracted_text": "detected text here"
# }
# =========================================================
@app.route("/extract-text", methods=["POST"], cors=True, content_types=["application/json"])
def extract_text():
    try:
        body = get_json_body()
        image_bytes, error = validate_base64_image(body)

        if error:
            app.log.warning(f"/outch, extract-text validation failed: {error}")
            return json_response(
                status_code=400,
                success=False,
                message=error
            )

        app.log.info(f"/extract-text received image with {len(image_bytes)} bytes.")

        # =====================================================
        # TODO (MEMBER 2):
        # Use AWS Rekognition here to detect text from image_bytes.
        # Replace ONLY the placeholder below.
        # =====================================================
        response = rekognition_client.detect_text(Image={"Bytes": image_bytes})

        lines = []
        for item in response.get("TextDetections", []):
            if item.get("Type") == "LINE":
                detected = item.get("DetectedText", "").strip()
                if detected:
                    lines.append(detected)

        extracted_text = " ".join(lines).strip()

        return json_response(
            status_code=200,
            success=True,
            message="Image accepted successfully, everything is going well.",
            data={
                "extracted_text": extracted_text
            }
        )

    except Exception as e:
        app.log.exception("Unexpected error in /extract-text")
        return json_response(
            status_code=500,
            success=False,
            message="Ouch, internal server error while processing /extract-text.",
            data={"details": str(e)}
        )


# =========================================================
# ROUTE 4: TRANSLATE TEXT
#
# NOTE FOR MEMBER 2 (AI Services):
# Edit ONLY the TODO section inside this function.
# Replace the placeholder with AWS Translate logic.
#
# Expected output in data:
# {
#   "original_text": "...",
#   "translated_text": "...",
#   "target_language": "es"
# }
# =========================================================
@app.route("/translate", methods=["POST"], cors=True, content_types=["application/json"])
def translate_text():
    try:
        body = get_json_body()

        text_value, text_error = validate_text(body)
        if text_error:
            app.log.warning(f"/Ouch, translate validation failed: {text_error}")
            return json_response(
                status_code=400,
                success=False,
                message=text_error
            )

        target_language, lang_error = validate_target_language(body)
        if lang_error:
            app.log.warning(f"/ouch, translate validation failed: {lang_error}")
            return json_response(
                status_code=400,
                success=False,
                message=lang_error
            )

        app.log.info(f'/translate received text="{text_value}" target_language="{target_language}"')

        # =====================================================
        # TODO (MEMBER 2):
        # Use AWS Translate here.
        # Replace ONLY the placeholder below.
        # =====================================================
        response = translate_client.translate_text(
            Text=text_value,
            SourceLanguageCode="auto",
            TargetLanguageCode=target_language
        )

        translated_text = response.get("TranslatedText", "")

        return json_response(
            status_code=200,
            success=True,
            message="Text accepted successfully, you are doing great!",
            data={
                "original_text": text_value,
                "translated_text": translated_text,
                "target_language": target_language
            }
        )

    except Exception as e:
        app.log.exception("Unexpected error in /translate")
        return json_response(
            status_code=500,
            success=False,
            message="Ouch, internal server error while processing /translate.",
            data={"details": str(e)}
        )


# =========================================================
# ROUTE 5: PROCESS IMAGE
#
# NOTE FOR MEMBER 3 (FRONTEND):
# This is the MAIN route to use from the web UI.
#
# Request body:
# {
#   "image": "BASE64_IMAGE_HERE",
#   "target_language": "es"
# }
#
# Read results from:
# data.extracted_text
# data.translated_text
# data.target_language
#
# NOTE FOR MEMBER 2 (AI Services):
# Replace the TODO sections only.
#
# NOTE FOR MEMBER 5 (Architecture / Testing):
# Use this route in the end-to-end interaction diagram and tests.
# =========================================================
@app.route("/process-image", methods=["POST"], cors=True, content_types=["application/json"])
def process_image():
    try:
        body = get_json_body()

        image_bytes, image_error = validate_base64_image(body)
        if image_error:
            app.log.warning(f"/Ouch, process-image validation failed: {image_error}")
            return json_response(
                status_code=400,
                success=False,
                message=image_error
            )

        target_language, lang_error = validate_target_language(body)
        if lang_error:
            app.log.warning(f"/Uh oh, process-image validation failed: {lang_error}")
            return json_response(
                status_code=400,
                success=False,
                message=lang_error
            )

        app.log.info(
            f"/process-image received image with {len(image_bytes)} bytes and target_language={target_language}"
        )

        # =====================================================
        # TODO (MEMBER 2):
        # Step 1: Extract text from image_bytes using Rekognition.
        # Replace ONLY the placeholder below.
        # =====================================================
        response = rekognition_client.detect_text(Image={"Bytes": image_bytes})

        lines = []
        for item in response.get("TextDetections", []):
            if item.get("Type") == "LINE":
                detected = item.get("DetectedText", "").strip()
                if detected:
                    lines.append(detected)

        extracted_text = " ".join(lines).strip()

        if not extracted_text:
            return json_response(
                status_code=200,
                success=True,
                message="No text was detected in the image.",
                data={
                    "extracted_text": "",
                    "translated_text": "",
                    "target_language": target_language
                }
            )

        # =====================================================
        # TODO (MEMBER 2):
        # Step 2: Translate extracted_text using AWS Translate.
        # Replace ONLY the placeholder below.
        # =====================================================
        translation_response = translate_client.translate_text(
            Text=extracted_text,
            SourceLanguageCode="auto",
            TargetLanguageCode=target_language
        )

        translated_text = translation_response.get("TranslatedText", "")

        # =========================================================
        # FOR MEMBER 4 (Cloud / Data):
        # =========================================================

        # generating a random UUID as unique image name
        unique = uuid.uuid4()
        file_name = f"{unique.hex}.jpg"

        # ============ START S3 ============
        try:
            s3_client.put_object(
                Bucket = S3_BUCKET,
                Body = image_bytes,
                Key = file_name,
                ContentType = "image/jpeg"
            )
        except Exception as e:
            app.log.error(f"S3 error: {e}")
            
        # ============ END S3 ============

        # ============ START DynamoDB ============
        try:
            table.put_item(Item = {
                "request_id": str(unique),
                # The method "utcnow" in class "datetime" is deprecated
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "original_text": extracted_text,
                "translated_text": translated_text,
                "target_language": target_language,
                "S3_BUCKET_name": S3_BUCKET,
                "image_name": file_name
            })
        except Exception as e:
            app.log.error(f"DynamoDB error: {e}")
        
        # ============ END DynamoDB ============
        # ======================== END MEMBER 4 ========================


        return json_response(
            status_code=200,
            success=True,
            message="Today, is a lucky day, the image has been accepted successfully.",
            data={
                "extracted_text": extracted_text,
                "translated_text": translated_text,
                "target_language": target_language
            }
        )

    except Exception as e:
        app.log.exception("Unexpected error in /process-image")
        return json_response(
            status_code=500,
            success=False,
            message="Ouch, internal server error while processing /process-image.",
            data={"details": str(e)}
        )
