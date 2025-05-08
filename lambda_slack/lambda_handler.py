import os
import json
import logging
import datetime
import boto3
from openai import OpenAI
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_bolt.adapter.aws_lambda.lambda_s3_oauth_flow import LambdaS3OAuthFlow


SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


app = App(
    process_before_response=True,
    oauth_flow=LambdaS3OAuthFlow()
)

ddb = boto3.resource('dynamodb')
users_id_table = ddb.Table(os.environ['DDB_USERS_ID'])
users_email_table = ddb.Table(os.environ['DDB_USERS_EMAIL'])
public_chats_table = ddb.Table(os.environ['DDB_PUBLIC_CHATS'])
private_chats_table = ddb.Table(os.environ['DDB_PRIVATE_CHATS'])

OPENAI_MODEL = os.environ['OPENAI_MODEL']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
MAX_CHAT_LENGTH = int(os.environ['MAX_CHAT_LENGTH'])
SLACK_EVENTS = os.environ['SLACK_EVENTS'].split(',')
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_URL = os.environ.get("SLACK_APP_URL")

STRIPE_MONTHLY_LINK= os.environ['STRIPE_MONTHLY_LINK']
STRIPE_ANNUAL_LINK= os.environ['STRIPE_ANNUAL_LINK']
STRIPE_LIFETIME_LINK= os.environ['STRIPE_LIFETIME_LINK']


def start_chat():
    return [
        {"role": "system", "content": "You are a helpful assistant."}
    ]


def get_openai_response(chat):
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=chat
    )
    logging.info(f"OpenAI response: {response}")
    return response


def get_openai_message_content(response):
    try:
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error getting OpenAI message content: {e}")
        return "Sorry, we are unable to process your request at this time. The OpenAI API is currently unavailable. Please try again later."


def add_to_chat(chat, role, content):
    chat.append(
        {"role": role, "content": content}
    )
    logging.info(f'add_to_chat: {chat}')
    return chat


def trim_chat(chat, max_length=MAX_CHAT_LENGTH):
    if len(chat) > max_length:
        del(chat[1:3])
        return chat
    logging.info(f"Chat length: {len(chat)}")
    return chat
    

def get_ddb_item(table, key_name, key_value):
    response = table.get_item(
        Key={key_name: key_value}
    )
    logging.info(f"get_ddb_item response: {response}")
    return response.get("Item")


def put_ddb_item(table, item):
    response = table.put_item(
        Item=item
    )
    logging.info(f"put_ddb_item response: {response}")
    return response
    

def get_chat_from_ddb_item(item):
    if item:
        logging.info(f"get_chat_from_ddb_item: {item}")
        return item.get("chat")
    else:
        logging.info(f"get_chat_from_ddb_item: no item found")
        return []


def save_chat_to_ddb(table, key_name, key_value, chat):
    ddb_item = {
        key_name: key_value,
        'chat': chat,
    }
    logging.info(f'save_chat_to_ddb: {table} {ddb_item}')
    return put_ddb_item(table, ddb_item)


def get_timestamp():
    return round(datetime.datetime.utcnow().timestamp())


def add_new_user(slack_id, email):
    slack_install_timestamp = get_timestamp()
    users_email_ddb_item = get_ddb_item(users_email_table, 'email', email)
    logging.info(f"add_new_user users_email_ddb_item: {users_email_ddb_item}")
    if not users_email_ddb_item:
        users_email_ddb_item = {
            'email': email,
            'workspaces':[
                slack_id
            ] 
        }
    else:
        if 'workspaces' not in users_email_ddb_item:
            users_email_ddb_item['workspaces'] = []
        users_email_ddb_item['workspaces'].append(slack_id)

    response = put_ddb_item(users_email_table, users_email_ddb_item)
    logging.info(f"add_new_user users_email_ddb_item: {users_email_ddb_item}")

    users_id_ddb_item = {
        'slack_id': slack_id,
        'email': email,
        'active': True, 
        'plan_type': 'trial',  
        'slack_install_timestamp': slack_install_timestamp,
    }
    response = put_ddb_item(users_id_table, users_id_ddb_item)
    logging.info(f"add_new_user users_id_ddb_item: {users_id_ddb_item}")
    return users_id_ddb_item


def get_public_chat_id(event):
    thread_ts = event.get("thread_ts")
    if not thread_ts:
        thread_ts = event.get("ts")
    team_id = event.get("team")
    channel_id = event.get("channel")
    return f'{team_id}-{channel_id}-{thread_ts}'


def get_private_chat_id(event):
    team_id = event.get("team")
    channel_id = event.get("channel")
    user_id = event.get("user")
    return f'{team_id}-{channel_id}-{user_id}'


def get_slack_user_info(client, user_id):
    try:
        result = client.users_info(
            user=user_id
        )
    except Exception as e:
        logging.error(f'get_slack_users_info error {e}')
    else:
        logging.info(f'get_slack_users_info info {result}')
        return result


def get_email(slack_user_info):
    try:
        return slack_user_info.get('user').get('profile').get('email')
    except AttributeError:
        return None


def get_slack_id(slack_user_info):
    try:
        slack_user_id = slack_user_info.get('user').get('id')
        slack_team_id = slack_user_info.get('user').get('team_id')
    except AttributeError:
        return None
    else:
        return f"{slack_team_id}-{slack_user_id}"


def get_user_record(event):
    slack_id = f'{event.get("team")}-{event.get("user")}'
    logging.info(f'get_user_record slack_id: {slack_id}')
    user_record = get_ddb_item(users_id_table, "slack_id", slack_id)
    logging.info(f'get_user_record: {user_record}')
    return user_record


def slack_challenge_response(challenge):
    return {
        'statusCode': 200,
        'body': json.dumps({'challenge': challenge}),
        'headers': {
                "Content-Type": "application/json"
        },
    }


def default_response(message="Successs"):
    logging.info(f'default_response: {message}')
    return {
        "statusCode": 200,
        "body": json.dumps({"message": message}),
        "headers": {
            "X-Slack-No-Retry": "1"
        }
    }


def get_inactive_message():
    return "We're thrilled you've been enjoying Bounce! Your free trial has wrapped up, but there's more value in store. Swing by the Home tab to continue taking advantage of enhanced productivity – subscribe now to keep bouncing with us! :rocket:"


def get_home_view(plan_type, active):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":wave: Hi! I'm Bounce, your ChatGPT for Slack app!",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "We are always improving! Click the button below to get the latest features.",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Update now",
                    },
                    "url": SLACK_APP_URL,
                },
            ],
        },
    ]
    if plan_type == "paid":
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Thanks for subscribing! Please share with your friends and colleagues!",
                },
            }
        )
        return {
            "type": "home",
            "callback_id": "home_view",
            "blocks": blocks
        }

    if plan_type == "trial":
        if active:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "We hope you are enjoying your free trial!",
                    },
                }
            )
        else:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Your free trial has expired. Subscribe now to continue using Bounce.",
                    },
                }
            )


    blocks.extend([
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Click one of the buttons below to start your subscription!",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Lifetime access for only $100",
                    },
                    "url": STRIPE_LIFETIME_LINK,
                },
            ],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Annual access for $50/year",
                    },
                    "url": STRIPE_ANNUAL_LINK,
                },
            ],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Monthly access for $5/month",
                    },
                    "url": STRIPE_MONTHLY_LINK,
                },
            ],
        },
    ])
    return {
        "type": "home",
        "callback_id": "home_view",
        "blocks": blocks
    }


@app.event("app_mention")
def app_mention_event(event, say):
    user_record = get_user_record(event)
    thread_ts = event.get("thread_ts")

    if user_record and user_record.get("active"):
        if thread_ts:
            public_chat_id = get_public_chat_id(event)
            chat = get_chat_from_ddb_item(get_ddb_item(public_chats_table, "public_chat_id", public_chat_id))
            logging.info(f"Retrieved existing public chat: {public_chat_id}")
        else:
            thread_ts = event.get("ts")
            public_chat_id = get_public_chat_id(event)
            logging.info(f"Starting new public chat: {public_chat_id}")
            chat = start_chat()

        chat = add_to_chat(chat, "user", event.get("text"))
        openai_message = get_openai_message_content(get_openai_response(chat))
        say(openai_message, thread_ts=thread_ts)
        chat = add_to_chat(chat, "assistant", openai_message)
        chat = trim_chat(chat)
        save_chat_to_ddb(public_chats_table, "public_chat_id", public_chat_id, chat)
    else:
        if thread_ts:
            say(get_inactive_message(), thread_ts=thread_ts)
        else:
            say(get_inactive_message(), thread_ts=event.get("ts"))


@app.event("message")
def message_event(event, say, logger):
    logging.info(f"message_event event {event}")
    user_id = event.get("user")
    logging.info(f"message_event user_id {user_id}")

    user_record = get_user_record(event)
    channel = event.get("channel")
    
    if event.get("channel_type") == "im":
        if user_record and user_record.get("active"):
            private_chat_id = get_private_chat_id(event)
            chat = get_chat_from_ddb_item(get_ddb_item(private_chats_table, "private_chat_id", private_chat_id))
            if not chat:
                logging.info(f"starting new private chat: {private_chat_id}")
                chat = start_chat()
            else:
                logging.info(f"retrieved existing private chat: {private_chat_id}")
                
            chat = add_to_chat(chat, "user", event.get("text"))
            openai_message = get_openai_message_content(get_openai_response(chat))
            say(openai_message, channel=channel)
            chat = add_to_chat(chat, "assistant", openai_message)
            chat = trim_chat(chat)
            save_chat_to_ddb(private_chats_table, "private_chat_id", private_chat_id, chat)
        else:
            say(get_inactive_message(), channel=channel)


@app.event("app_home_opened")
def app_home_opened_event(client, event):
    user_id = event.get("user")
    slack_user_info = get_slack_user_info(client, user_id)
    slack_id = get_slack_id(slack_user_info)
    users_id_item = get_ddb_item(users_id_table, "slack_id", slack_id)

    if not users_id_item:
        email = get_email(slack_user_info)
        users_id_item = add_new_user(slack_id, email)

    plan_type = users_id_item.get("plan_type")
    active = users_id_item.get("active")
    response = client.views_publish(
        user_id=user_id,
        view=get_home_view(plan_type, active)
    )


def handler(event, context):
    logging.info(f'event: {event}')
    logging.info(f'context: {context}')
    headers = event.get("headers")
    logging.info(f'headers: {headers}')

    if headers and "x-slack-retry-num" in headers:
        return default_response("Ignore retry")

    body = event.get("body")
    if body:
        body = json.loads(body)

        if body.get("challenge"):
            return slack_challenge_response(body.get("challenge"))

        if body.get("event").get("bot_id"):
            return default_response("Ignore bot")

        if body.get("event").get("type") not in SLACK_EVENTS:
            return default_response("Ignore event")

    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)