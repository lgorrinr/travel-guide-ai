# Travel Guide Backend Handoff

## Team Member
Lissette – Backend (Chalice + REST API)

## Main file to edit
- travel-guide/app.py

## What is already completed
- Chalice backend project created
- API routes created
- Input validation added
- Consistent JSON response structure added
- Error handling and logging added
- Local test routes prepared

## Routes

### 1. GET /
Health check route

Response example:
{
  "success": true,
  "message": "Travel Guide API is running.",
  "data": {
    "service": "travel-guide-backend",
    "owner": "Lissette",
    "available_routes": [
      "GET /",
      "POST /extract-text",
      "POST /translate",
      "POST /process-image"
    ]
  }
}

### 2. POST /extract-text
Request body:
{
  "image": "BASE64_IMAGE_HERE"
}

Current status:
- validation completed
- placeholder response only

TODO for Member 2:
- replace placeholder in /extract-text with AWS Rekognition text extraction

### 3. POST /translate
Request body:
{
  "text": "Hello",
  "target_language": "es"
}

Current status:
- validation completed
- placeholder response only

TODO for Member 2:
- replace placeholder in /translate with AWS Translate logic

### 4. POST /process-image
Request body:
{
  "image": "BASE64_IMAGE_HERE",
  "target_language": "es"
}

Current status:
- validation completed
- placeholder response only

TODO for Member 2:
1. Extract text from image
2. Translate extracted text

## Notes for Member 3 (Frontend)
Use POST /process-image as the main route.
Read response from:
- data.extracted_text
- data.translated_text
- data.target_language

## Notes for Member 4 (Cloud / Data)
Shared constant in code:
- S3_BUCKET = "travel-guide-images"

Please confirm final bucket name and permissions.

## Notes for Member 5 (Architecture / Testing)
System flow:
Frontend -> Chalice API -> Rekognition / Translate -> JSON Response

Routes to include in diagrams:
- GET /
- POST /extract-text
- POST /translate
- POST /process-image
