import os
import json
from datetime import datetime, timedelta
import base64
import hmac
import hashlib
from cgi import parse_header
import boto3


STRIPE_SECRET = os.environ.get('STRIPE_SECRET')


class PutEventError(Exception):
    """Raised when Put Events Failed"""
    pass

def handler(event, _context):
    """Webhook function"""
    print(event)
    headers = event.get('headers')

    # Input validation
    try:
        json_payload = get_json_payload(event=event)
    except ValueError as err:
        print_error(f'400 Bad Request - {err}', headers)
        return {'statusCode': 400, 'body': str(err)}
    except BaseException as err:  # Unexpected Error
        print_error('500 Internal Server Error\n' +
                    f'Unexpected error: {err}, {type(err)}', headers)
        return {'statusCode': 500, 'body': 'Internal Server Error'}

    try:

        timestamp, signatures = parse_signature(
            signature_header=headers.get('stripe-signature'))

        if not timestamp or not timestamp_is_valid(timestamp):
            print_error('400 Bad Request - Invalid timestamp', headers)
            return {
                'statusCode': 400,
                'body': 'Invalid timestamp'
            }

        if not contains_valid_signature(
                payload=json_payload,
                timestamp=timestamp,
                signatures=signatures):
            print_error('401 Unauthorized - Invalid Signature', headers)
            return {'statusCode': 401, 'body': 'Invalid Signature'}

        json_dict = json.loads(json_payload)
        email = get_email(json_dict)
        print(f'Email: {email}')

        return {'statusCode': 202, 'body': 'Success'}

    except PutEventError as err:
        print_error(f'500 Put Events Error - {err}', headers)
        return {'statusCode': 500, 'body': 'Internal Server Error - The request was rejected by Amazon EventBridge API'}

    except BaseException as err:  # Unexpected Error
        print_error('500 Client Error\n' +
                    f'Unexpected error: {err}, {type(err)}', headers)
        return {'statusCode': 500, 'body': 'Internal Server Error'}


def get_json_payload(event):
    """Get JSON string from payload"""
    content_type = get_content_type(event.get('headers', {}))
    if content_type != 'application/json':
        raise ValueError('Unsupported content-type')

    payload = normalize_payload(
        raw_payload=event.get('body'),
        is_base64_encoded=event['isBase64Encoded'])

    try:
        json.loads(payload)

    except ValueError as err:
        raise ValueError('Invalid JSON payload') from err

    return payload


def normalize_payload(raw_payload, is_base64_encoded):
    """Decode payload if needed"""
    if raw_payload is None:
        raise ValueError('Missing event body')
    if is_base64_encoded:
        return base64.b64decode(raw_payload).decode('utf-8')
    return raw_payload


def contains_valid_signature(payload, timestamp, signatures):
    """Check for the payload signature
       Stripe documentation: https://stripe.com/docs/webhooks/signatures
    """
    payload_bytes = get_payload_bytes(
        timestamp=timestamp,
        payload=payload
    )
    computed_signature = compute_signature(
        payload_bytes=payload_bytes, secret=STRIPE_SECRET)
    return any(
        hmac.compare_digest(event_signature, computed_signature)
        for event_signature in signatures
    )


def get_payload_bytes(timestamp, payload):
    """Get payload bytes to feed hash function"""
    return (timestamp + "." + payload).encode()


def compute_signature(payload_bytes, secret):
    """Compute HMAC-SHA256"""
    return hmac.new(key=secret.encode(), msg=payload_bytes, digestmod=hashlib.sha256).hexdigest()


def parse_signature(signature_header):
    """
        Parse signature from hearders based on:
        https://stripe.com/docs/webhooks/signatures#prepare-payload
    """
    if not signature_header:
        return None, None

    header_elements = signature_header.split(',')
    timestamp, signatures = None, []

    for element in header_elements:
        [k, v] = element.split('=')
        if k == 't':
            timestamp = v
        # Stripe will send all valid signatures as a v1=<signature>
        if k == 'v1':
            signatures.append(v)

    return timestamp, signatures


def timestamp_is_valid(timestamp):
    """Check whether incoming timestamp is not too old (<5min old)"""
    current_time = datetime.today()
    stripe_timestamp = datetime.fromtimestamp(int(timestamp))

    diff = current_time - stripe_timestamp

    # Time diff is less than 5 minutes
    return diff < timedelta(minutes=5)


def get_content_type(headers):
    """Helper function to parse content-type from the header"""
    raw_content_type = headers.get('content-type')

    if raw_content_type is None:
        return None
    content_type, _ = parse_header(raw_content_type)
    return content_type


def print_error(message, headers):
    """Helper function to print errors"""
    print(f'ERROR: {message}\nHeaders: {str(headers)}')


def get_email(json_dict):
    return json_dict["data"]["object"]["charges"]["data"][0]["billing_details"]["email"]