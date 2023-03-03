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
private_chats = dict()
public_chats = dict()


def start_chat():
    return [
        {"role": "system", "content": "You are a helpful assistant."}
    ]


def get_openai_response(chat):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat
    )
    print(response)
    return response["choices"][0]["message"]["content"]


def trim_chat(chat):
    if len(chat) >= 5:
        del(chat[1:3])
        return chat
    return chat
    

@app.event("app_mention")
def app_mention_event(event, say):
    team_id = event.get("team")
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")

    if thread_ts:
        public_chat_id = f'{team_id}-{channel_id}-{thread_ts}'
        print(f"Retrieving existing public thread: {public_chat_id}")
        chat = public_chats[public_chat_id]
    else:
        thread_ts = event.get("ts")
        public_chat_id = f'{team_id}-{channel_id}-{thread_ts}'
        print(f"Starting new public thread: {public_chat_id}")
        chat = start_chat()

    user_input = event.get("text")
    chat.append(
        {"role": "user", "content": user_input}
    )
    print(f"thread_ts: {thread_ts}")
    openai_response = get_openai_response(chat)
    say(openai_response, thread_ts=thread_ts)
    chat.append(
        {"role": "assistant", "content": openai_response}
    )
    chat = trim_chat(chat)
    public_chats[public_chat_id] = chat
    print(chat)
    print(public_chats)


@app.event("message")
def message_event(event, say):
    channel_type = event.get("channel_type")
    if channel_type == "im":
        team_id = event.get("team")
        channel_id = event.get("channel")
        user_id = event.get("user")
        private_chat_id = f'{team_id}-{channel_id}-{user_id}'

        if private_chat_id in private_chats:
            print("Retrieving existing private chat")
            chat = private_chats[private_chat_id]
        else:
            print("Starting new private chat")
            chat = start_chat()
            
        user_input = event.get("text")
        chat.append(
            {"role": "user", "content": user_input}
        )
        openai_response = get_openai_response(chat)
        say(openai_response, channel=channel_id)
        chat.append(
            {"role": "assistant", "content": openai_response}
        )
        chat = trim_chat(chat)
        private_chats[private_chat_id] = chat
        print(chat)
        print(private_chats)


#def respond_to_slack_within_3_seconds(body, ack):
#    ack("Let slack know app is processing request")

#app.event("app_mention")(
#    ack=respond_to_slack_within_3_seconds,
#    lazy=[app_mention_event]
#)

#app.event("message")(
#    ack=respond_to_slack_within_3_seconds,
#    lazy=[message_event]
#)

#def get_sqs_message(slack_event):
#    """
#    Pass slack event into SQS message for downstream processing
#    """
#    return json.dumps(slack_event)
#
#
#def send_sqs_message(sqs_message):
#    """
#    Send SQS message to SQS queue
#    """
#    sqs = boto3.client('sqs')
#    sqs.send_message(
#        QueueUrl="https://sqs.us-east-1.amazonaws.com/846078712375/ApiLambdaStack-Queue4A7E3555-5oHbpDACP4F4",
#        MessageBody=sqs_message
#    )


def challenge_response(challenge):
    return {
        'statusCode': 200,
        'body': json.dumps({'challenge': challenge}),
        'headers': {
                "Content-Type": "application/json"
        },
    }


def default_response(message="Successs"):
    print(message)
    return {
        "statusCode": 200,
        "body": json.dumps({"message": message}),
        "headers": {
            "X-Slack-No-Retry": "1"
        }
    }


def handler(event, context):
    print(event)
    print(context)
    headers = event.get("headers")
    if "x-slack-retry-num" in headers:
        return default_response("Ignore retry")

    body = event.get("body")
    if body:
        body = json.loads(body)

        if body.get("challenge"):
            return challenge_response(body.get("challenge"))

        bot_id = body.get("event").get("bot_id")
        if bot_id:
            return default_response("Ignore bot")

        event_type = body.get("event").get("type")
        if event_type not in ["app_mention", "message"]:
            return default_response("Ignore event")

    return SlackRequestHandler(app).handle(event, context)