import os
import json
import boto3
import base64
import hmac
import hashlib
import logging
from cgi import parse_header
from datetime import datetime, timedelta


log = logging.getLogger()
log.setLevel(logging.INFO)

STRIPE_SECRET = os.environ.get('STRIPE_SECRET')

ddb = boto3.resource('dynamodb')
users_id_table = ddb.Table(os.environ['DDB_USERS_ID'])
users_email_table = ddb.Table(os.environ['DDB_USERS_EMAIL'])


def get_json_payload(event):
    """
    Get JSON string from payload
    
    Args:
        event (dict): Lambda event payload
    Returns:
        str: JSON string
    """
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
    """
    Decode payload if needed
    
    Args:
        raw_payload (str): Raw payload
        is_base64_encoded (bool): Whether payload is base64 encoded
    Returns:
        str: Decoded payload
    """
    if raw_payload is None:
        raise ValueError('Missing event body')
    if is_base64_encoded:
        return base64.b64decode(raw_payload).decode('utf-8')
    return raw_payload


def contains_valid_signature(payload, timestamp, signatures):
    """
    Check for the payload signature
    Stripe documentation: https://stripe.com/docs/webhooks/signatures

    Args:
        payload (str): JSON payload
        timestamp (str): Stripe timestamp
        signatures (list): List of signatures
    Returns:
        bool: Whether payload contains a valid signature
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
    """
    Get payload bytes to feed hash function

    Args:
        timestamp (str): Stripe timestamp
        payload (str): JSON payload
    Returns:
        bytes: Payload in bytes
    """
    return (timestamp + "." + payload).encode()


def compute_signature(payload_bytes, secret):
    """
    Compute HMAC-SHA256 signature

    Args:
        payload_bytes (bytes): Payload in bytes
        secret (str): Stripe secret
    Returns:
        str: HMAC-SHA256 signature
    """
    return hmac.new(key=secret.encode(), msg=payload_bytes, digestmod=hashlib.sha256).hexdigest()


def parse_signature(signature_header):
    """
    Parse signature from hearders based on:
    https://stripe.com/docs/webhooks/signatures#prepare-payload

    Args:
        signature_header (str): Stripe signature header
    Returns:
        tuple: Tuple of timestamp and signatures
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
    """
    Check whether incoming timestamp is not too old (<5min old)

    Args:
        timestamp (str): Stripe timestamp

    Returns:
        bool: Whether timestamp is valid
    """
    current_time = datetime.today()
    stripe_timestamp = datetime.fromtimestamp(int(timestamp))

    diff = current_time - stripe_timestamp

    # Time diff is less than 5 minutes
    return diff < timedelta(minutes=5)


def get_content_type(headers):
    """
    Helper function to parse content-type from the header

    Args:
        headers (dict): Lambda event headers
    Returns:
        str: Content-type
    """
    raw_content_type = headers.get('content-type')

    if raw_content_type is None:
        return None
    content_type, _ = parse_header(raw_content_type)
    return content_type


def get_email(json_dict):
    """
    Get email from Stripe JSON payload

    Args:
        json_dict (dict): Stripe JSON payload
    Returns:
        str: Email
    """
    try:
        return json_dict["data"]["object"]["charges"]["data"][0]["billing_details"]["email"]
    except KeyError as e:
        return ""
    

def get_payment_timestamp(json_dict):
    """
    Get timestamp from Stripe JSON payload

    Args:
        json_dict (dict): Stripe JSON payload
    Returns:
        int: Epoch payment timestamp
    """
    try:
        return json_dict["created"]
    except KeyError as e:
        return 0


def get_ddb_item(table, key_name, key_value):
    response = table.get_item(
        Key={key_name: key_value}
    )
    logging.info(f"get_ddb_item response: {response}")
    return response.get("Item")


def get_slack_ids(email):
    users_email_ddb_item = get_ddb_item(users_email_table, 'email', email)
    return users_email_ddb_item.get('workspaces', [])


def update_users_id_table(slack_ids, stripe_payment_timestamp, email):
    for slack_id in slack_ids:
        response = users_id_table.update_item(
            Key={"slack_id": slack_id},
            UpdateExpression='SET active = :activeValue, plan_type = :planTypeValue, payment_timestamp = :paymentTimestampValue, email = :emailValue',
            ExpressionAttributeValues={
                ':activeValue': True,
                ':planTypeValue': 'paid',
                ':paymentTimestampValue': stripe_payment_timestamp,
                ':emailValue': email
            }
        )
        log.info(f"update_users_id_table response: {response}")
        
def handler(event, _context):
    log.info(f'event: {event}')
    headers = event.get('headers')
    log.info(f'headers: {event}')

    # Input validation
    try:
        json_payload = get_json_payload(event=event)
    except ValueError as err:
        log.error(f'400 Bad Request - {err}', headers)
        return {'statusCode': 400, 'body': str(err)}
    except BaseException as err:  # Unexpected Error
        log.error(f'500 Internal Server Error\nUnexpected error: {err}, {type(err)}')
        return {'statusCode': 500, 'body': 'Internal Server Error'}

    try:

        timestamp, signatures = parse_signature(signature_header=headers.get('stripe-signature'))

        if not timestamp or not timestamp_is_valid(timestamp):
            log.error('400 Bad Request - Invalid timestamp')
            return {
                'statusCode': 400,
                'body': 'Invalid timestamp'
            }

        if not contains_valid_signature(payload=json_payload, timestamp=timestamp, signatures=signatures):
            log.error('401 Unauthorized - Invalid Signature')
            return {'statusCode': 401, 'body': 'Invalid Signature'}

        json_dict = json.loads(json_payload)
        email = get_email(json_dict)
        stripe_payment_timestamp = get_payment_timestamp(json_dict)
        slack_ids = get_slack_ids(email)

        log.info(f'Stripe payment timestamp: {stripe_payment_timestamp}')
        log.info(f'User email: {email}')
        log.info(f'Slack workspaces: {email}')

        update_users_id_table(slack_ids, stripe_payment_timestamp, email)
        return {'statusCode': 202, 'body': 'Stripe payment event successfully processed'}

    except Exception as e:
        log.error(f'500 Internal Server Error - {e}')
        return {'statusCode': 500, 'body': 'Internal Server Error'}

    except BaseException as err:  # Unexpected Error
        log.error(f'500 Client Error\nUnexpected error: {err}, {type(err)}')
        return {'statusCode': 500, 'body': 'Internal Server Error'}