# Travel Guide AI

Travel Guide is an AI-powered image translation app for tourists.

## Project structure

- backend/ → Chalice API
- frontend/ → Web UI
- docs/ → diagrams and documentation

## Main backend routes

- GET /
- POST /extract-text
- POST /translate
- POST /process-image

## Team roles

- Lissette → Backend
- Jason → AI Services
- Wardatul → Frontend
- Bin → Cloud / Data
- Samer → Architecture / Testing

# Local:
- Go to the folder 'backend' under the project folder: cd backend
- active virtual environment: pipenv shell
- install dependencys: pipenv install
- Run Chalice and test in local (when everything done): chalice local

# AWS Cloud Documentation: Set up
- make sure you have an AWS account
- check AWS access key In termial(under backend path): aws configure list
- if your access key and secret key doesn't work:
- create new one in the exist user page in AWS, then type aws configure in terminal and type new access key and secret key.

## 1. Create S3 Bucket
- Bucket Name: 'travel-guide-images'
- Region Name: 'us-east-1'
- Purpose: Store uploaded images.

## 2. Create DynamoDB Table
- DynamoDB Name: 'TravelGuideTranslations'
- Primary Key: 'request_id' (String)
- Sort Key: 'timestamp' (String)
- Purpose: Insert each translation into the table.

## 3. Create IAM Policy
- Name: 'TravelGuideChalicePolicy'
- Permissions: 'rekognition:DetectText', 'translate:TranslateText', 's3:PutObject', 'dynamodb:PutItem'
- JSON: choose JSON and copy and paste the following json code
- PS: remember to change "arn:aws:s3:::your_S3_bucket_name/*" in 's3:PutObject'
- PS: remember to change "arn:aws:dynamodb:us-east-1:your_12digits_aws_id:table/TravelGuideTranslations" in 'dynamodb:PutItem'

## 4. Add permissions to exist users in IAM
- choose the exist user
- click on drop-down button to choose 'Add permissions'
- Choose radio button 'Attach policies directly'
- search 'TravelGuideChalicePolicy' and choose it.

```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "AllowRekognitionDetectTextAllowRekognitionDetectText",
			"Effect": "Allow",
			"Action": [
				"rekognition:DetectText"
			],
			"Resource": [
				"*"
			]
		},
		{
			"Sid": "AllowTranslateText",
			"Effect": "Allow",
			"Action": [
				"translate:TranslateText"
			],
			"Resource": [
				"*"
			]
		},
		{
			"Sid": "AllowS3PutObject",
			"Effect": "Allow",
			"Action": [
				"s3:PutObject"
			],
			"Resource": [
				"arn:aws:s3:::your_S3_bucket_name/*"
			]
		},
		{
			"Sid": "AllowDynamoDBPutItem",
			"Effect": "Allow",
			"Action": [
                "dynamodb:PutItem"
            ],
			"Resource": [
                "arn:aws:dynamodb:us-east-1:your_12digits_aws_id:table/TravelGuideTranslations"
            ]
		}
	]
}

