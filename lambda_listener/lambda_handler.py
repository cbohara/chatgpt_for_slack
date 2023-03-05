import time
import os
import json
import logging
import boto3
import openai
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
public_chats_table = ddb.Table(os.environ['DDB_PUBLIC_CHATS'])
private_chats_table = ddb.Table(os.environ['DDB_PRIVATE_CHATS'])

OPENAI_MODEL = os.environ['OPENAI_MODEL']
MAX_CHAT_LENGTH = int(os.environ['MAX_CHAT_LENGTH'])
SLACK_EVENTS = os.environ['SLACK_EVENTS'].split(',')


def start_chat():
    return [
        {"role": "system", "content": "You are a helpful assistant."}
    ]


def get_openai_response(chat):
    # TODO - Avoid hitting max token limit
    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=chat
    )
    logging.info(f"OpenAI response: {response}")
    return response


def get_openai_message_content(response):
    try:
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Error getting OpenAI message content: {e}")
        return "Sorry, we are unable to process your request at this time. The OpenAI API is currently unavailable. Please try again later."


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


def add_to_chat(chat, role, content):
    chat.append(
        {"role": role, "content": content}
    )
    logging.info(f'add_to_chat: {chat}')
    return chat


@app.event("app_mention")
def app_mention_event(event, say):
    thread_ts = event.get("thread_ts")
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


@app.event("message")
def message_event(event, say):
    if event.get("channel_type") == "im":
        private_chat_id = get_private_chat_id(event)
        chat = get_chat_from_ddb_item(get_ddb_item(private_chats_table, "private_chat_id", private_chat_id))
        if not chat:
            logging.info(f"Starting new private chat: {private_chat_id}")
            chat = start_chat()
        else:
            logging.info(f"Retrieved existing private chat: {private_chat_id}")

            
        chat = add_to_chat(chat, "user", event.get("text"))
        openai_message = get_openai_message_content(get_openai_response(chat))
        say(openai_message, channel=event.get("channel"))
        chat = add_to_chat(chat, "assistant", openai_message)
        chat = trim_chat(chat)
        save_chat_to_ddb(private_chats_table, "private_chat_id", private_chat_id, chat)


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


def handler(event, context):
    logging.info(f'event: {event}')
    logging.info(f'context: {context}')

    if event.get("headers") and "x-slack-retry-num" in event.get("headers"):
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

    return SlackRequestHandler(app).handle(event, context)