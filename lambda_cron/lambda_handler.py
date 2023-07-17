import os
import boto3
import logging
from boto3.dynamodb.conditions import Attr, Key
from datetime import datetime, timedelta


logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


FREE_TRIAL_DAYS = int(os.environ['FREE_TRIAL_DAYS'])
ddb = boto3.resource('dynamodb')
users_id_table = ddb.Table(os.environ['DDB_USERS_ID'])
current_datetime = datetime.utcnow()


def free_trial_completed(item, current_datetime):
    slack_install_timestamp = item.get('slack_install_timestamp')
    if not slack_install_timestamp:
        logging.warning("Item missing slack_install_timestamp")
        return False
    
    slack_install_datetime = datetime.fromtimestamp(int(slack_install_timestamp))
    trial_period = current_datetime - timedelta(days=FREE_TRIAL_DAYS)
    if slack_install_datetime < trial_period:
        logging.info("Free trial completed")
        return True
    logging.info("Free trial ongoing")
    return False


def handler(event, context):
    response = users_id_table.query(
        IndexName='plan_type_index',
        KeyConditionExpression=Key('plan_type').eq('trial'),
        FilterExpression=Attr('active').eq(True),
        ProjectionExpression='slack_id, active, email, plan_type, slack_install_timestamp'
    )
    
    items = response['Items']
    for item in items:
        logging.info(f"Processing item: {item}")
        if free_trial_completed(item, current_datetime):
            item['active'] = False
            users_id_table.put_item(Item=item)
