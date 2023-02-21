import json
import urllib.parse
import boto3


def get_email(body: str) -> str:
    """
    Get email from body
    """
    return body.split('=')[1]


def parse_email(encoded_email: str) -> str:
    """
    Convert email in url format to standard format
    """
    return urllib.parse.unquote(encoded_email)


def get_sqs_message(email: str) -> str:
    """
    Pass email into SQS message for downstream processing
    """
    return json.dumps({"email": email})


def send_sqs_message(sqs_message: str) -> None:
    """
    Send SQS message to SQS queue
    """
    sqs = boto3.client('sqs')
    sqs.send_message(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/846078712375/ApiLambdaStack-Queue4A7E3555-lJuhIaGkKrDt",
        MessageBody=sqs_message
    )


def handler(event, context):
    body = event['body']
    encoded_email = get_email(body)
    email = parse_email(encoded_email)
    sqs_message = get_sqs_message(email)
    send_sqs_message(sqs_message)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': 'https://www.mlpal.com'
        },
        'body': "Success! You've been added to our waitlist."
    }