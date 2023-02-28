import time
import os
import json
import logging
import boto3
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_bolt.adapter.aws_lambda.lambda_s3_oauth_flow import LambdaS3OAuthFlow

from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.chains.conversation.memory import ConversationalBufferWindowMemory


SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


app = App(
    process_before_response=True,
    oauth_flow=LambdaS3OAuthFlow()
)
private_chats = dict()
public_chats = dict()



def get_prompt():
    template = """Assistant is a large language model trained by OpenAI.

    Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

    Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

    Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

    {history}
    Human: {human_input}
    Assistant:"""
    return PromptTemplate(
        input_variables=["history", "human_input"], 
        template=template
    )


def start_chat():
    return LLMChain(
        llm=OpenAI(
            temperature=0,
            max_retries=0
        ), 
        prompt=get_prompt(), 
        verbose=True, 
        memory=ConversationalBufferWindowMemory(k=10),
    )



def respond_to_slack_within_3_seconds(body, ack):
    ack("Let slack know app is processing request")


# need to figure out how to avoid duplicate events
def app_mention_event(event, say, logger):
    team_id = event.get("team")
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")

    if thread_ts:
        print("Retrieving existing public thread")
        public_chat_id = f'{team_id}-{channel_id}-{thread_ts}'
        chat = public_chats[public_chat_id]
    else:
        print("Starting new public thread")
        thread_ts = event.get("event_ts")
        public_chat_id = f'{team_id}-{channel_id}-{thread_ts}'
        chat = start_chat()
        public_chats[public_chat_id] = chat

    user_input = event.get("text")
    openai_response = chat.predict(human_input=user_input)
    say(openai_response, thread_ts=thread_ts)


app.event("app_mention")(
    ack=respond_to_slack_within_3_seconds,
    lazy=[app_mention_event]
)


def message_event(event, say, logger):
    channel_type = event.get("channel_type")
    if channel_type == "im":
        team_id = event.get("team")
        channel_id = event.get("channel")
        user_id = event.get("user")
        private_chat_id = f'{team_id}-{channel_id}-{user_id}'

        if user_id in private_chats:
            print("Retrieving existing private chat")
            chat = private_chats[private_chat_id]
        else:
            print("Starting new private chat")
            chat = start_chat()
            private_chats[private_chat_id] = chat
            
        user_input = event.get("text")
        openai_response = chat.predict(human_input=user_input)
        say(openai_response, channel=channel_id)


app.event("message")(
    ack=respond_to_slack_within_3_seconds,
    lazy=[message_event]
)


def get_sqs_message(slack_event):
    """
    Pass slack event into SQS message for downstream processing
    """
    return json.dumps(slack_event)


def send_sqs_message(sqs_message):
    """
    Send SQS message to SQS queue
    """
    sqs = boto3.client('sqs')
    sqs.send_message(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/846078712375/ApiLambdaStack-Queue4A7E3555-5oHbpDACP4F4",
        MessageBody=sqs_message
    )


def challenge_response(challenge):
    return {
        'statusCode': 200,
        'body': json.dumps({'challenge': challenge}),
        'headers': {
                "Content-Type": "application/json"
        },
    }


def default_response(message="Successs"):
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
    if "X-Slack-Retry-Num" in headers:
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