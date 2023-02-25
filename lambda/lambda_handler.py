import os
import json
import logging
import boto3
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.chains.conversation.memory import ConversationalBufferWindowMemory


SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    process_before_response=True
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
        llm=OpenAI(temperature=0), 
        prompt=get_prompt(), 
        verbose=True, 
        memory=ConversationalBufferWindowMemory(k=20),
    )


def app_mention_event(event, say, logger):
    team_id = event.get("team")
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")

    if thread_ts:
        public_chat_id = f'{team_id}-{channel_id}-{thread_ts}'
        chat = public_chats[public_chat_id]
    else:
        thread_ts = event.get("event_ts")
        public_chat_id = f'{team_id}-{channel_id}-{thread_ts}'
        chat = start_chat()
        public_chats[public_chat_id] = chat

    user_input = event.get("text")
    openai_response = chat.predict(human_input=user_input)
    say(openai_response, thread_ts=thread_ts)


app.lazy_listener("app_mention")(app_mention_event)


def message_event(event, say, logger):
    channel_type = event.get("channel_type")
    if channel_type == "im":
        channel_id = event.get("channel")
        user_id = event.get("user")

        if user_id in private_chats:
            chat = private_chats[user_id]
        else:
            chat = start_chat()
            private_chats[user_id] = chat
            
        user_input = event.get("text")
        openai_response = chat.predict(human_input=user_input)
        say(openai_response, channel=channel_id)

app.lazy_listener("message")(message_event)


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


def handler(event, context):
    body = json.loads(event.get("body"))
    bot_id = body.get("event").get("bot_id")
    if bot_id:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Ignore bot"})
        }

    event_type = body.get("event").get("type")
    if event_type not in ["app_mention", "message"]:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Ignore event"})
        }

    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)