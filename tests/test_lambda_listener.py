import pytest
import boto3
from lambda_listener import lambda_handler
from moto import mock_dynamodb
from freezegun import freeze_time


def test_start_chat():
    chat = lambda_handler.start_chat()
    assert len(chat) == 1
    assert chat[0] == {"role": "system", "content": "You are a helpful assistant."}


@pytest.mark.openai_api
def test_get_openai_response():
    chat = lambda_handler.start_chat()
    response = lambda_handler.get_openai_response(chat)
    assert response.get("model") == "gpt-3.5-turbo-0301"


def test_get_openai_message_content(openai_response):
    message_content = lambda_handler.get_openai_message_content(openai_response)
    assert message_content == "Thank you! How may I assist you today?"

    openai_response = {"choices": []}
    assert lambda_handler.get_openai_message_content(openai_response) == "Sorry, we are unable to process your request at this time. The OpenAI API is currently unavailable. Please try again later."


def test_trim_chat_default_max_length():
    chat = lambda_handler.start_chat()
    assert len(lambda_handler.trim_chat(chat)) == 1

    chat.append({"role": "user", "content": "user input"})
    chat.append({"role": "assisatnt", "content": "assistant response"})
    assert len(lambda_handler.trim_chat(chat)) == 3

    chat.append({"role": "user", "content": "user input"})
    chat.append({"role": "assisatnt", "content": "assistant response"})
    assert len(lambda_handler.trim_chat(chat)) == 5

    chat.append({"role": "user", "content": "user input"})
    chat.append({"role": "assisatnt", "content": "assistant response"})
    assert len(lambda_handler.trim_chat(chat)) == 7

    chat.append({"role": "user", "content": "user input"})
    chat.append({"role": "assisatnt", "content": "assistant response"})
    assert len(lambda_handler.trim_chat(chat)) == 7


def test_trim_chat_config_max_length():
    chat = lambda_handler.start_chat()
    assert len(lambda_handler.trim_chat(chat, max_length=3)) == 1

    chat.append({"role": "user", "content": "user input"})
    chat.append({"role": "assisatnt", "content": "assistant response"})
    assert len(lambda_handler.trim_chat(chat, max_length=3)) == 3

    chat.append({"role": "user", "content": "user input"})
    chat.append({"role": "assisatnt", "content": "assistant response"})
    assert len(lambda_handler.trim_chat(chat, max_length=3)) == 3


def test_put_ddb_item_private_chats(dynamodb_mock, private_chats_item):
    table_name = 'test_private_chats'
    ddb_id = "private_chat_id"
    table = dynamodb_mock.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': ddb_id, 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': ddb_id, 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )
    table.put_item(Item=private_chats_item)
    response = lambda_handler.put_ddb_item(table, private_chats_item)
    assert response.get("ResponseMetadata").get("HTTPStatusCode") == 200


def test_get_ddb_item_private_chats(dynamodb_mock, private_chats_item):
    table_name = 'test_private_chats'
    ddb_id = "private_chat_id"
    table = dynamodb_mock.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': ddb_id, 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': ddb_id, 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )
    chat_id = private_chats_item.get(ddb_id)
    table.put_item(Item=private_chats_item)
    item = lambda_handler.get_ddb_item(table, ddb_id, chat_id)
    assert item.get(ddb_id) == chat_id

    item = lambda_handler.get_ddb_item(table, ddb_id, "nonexistent")
    assert not item


def test_get_chat_from_ddb_item(private_chats_item, chat):
    assert lambda_handler.get_chat_from_ddb_item(private_chats_item) == chat
    assert lambda_handler.get_chat_from_ddb_item({}) == []


def test_put_ddb_item_public_chats(dynamodb_mock, public_chats_item):
    table_name = 'test_public_chats'
    ddb_id = "public_chat_id"
    table = dynamodb_mock.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': ddb_id, 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': ddb_id, 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )
    table.put_item(Item=public_chats_item)
    response = lambda_handler.put_ddb_item(table, public_chats_item)
    assert response.get("ResponseMetadata").get("HTTPStatusCode") == 200


def test_get_ddb_item_public_chats(dynamodb_mock, public_chats_item):
    table_name = 'test_public_chats'
    ddb_id = "public_chat_id"
    table = dynamodb_mock.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': ddb_id, 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': ddb_id, 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )
    chat_id = public_chats_item.get(ddb_id)
    table.put_item(Item=public_chats_item)
    item = lambda_handler.get_ddb_item(table, ddb_id, chat_id)
    assert item.get("public_chat_id") == chat_id

    item = lambda_handler.get_ddb_item(table, "public_chat_id", "nonexistent")
    assert not item


def test_get_public_chat_id(app_mention_event_thread_exists, app_mention_event_thread_does_not_exist):
    assert lambda_handler.get_public_chat_id(app_mention_event_thread_exists) == "T04L47VTW0Z-C04L47VUPMX-1677959194.104609"
    assert lambda_handler.get_public_chat_id(app_mention_event_thread_does_not_exist) == "T04L47VTW0Z-C04L47VUPMX-1677959194.104609"


def test_add_user_input_to_chat(app_mention_event_thread_exists):
    chat = lambda_handler.start_chat()
    user_input = app_mention_event_thread_exists["text"]
    chat = lambda_handler.add_to_chat(chat, "user", user_input)
    assert len(chat) == 2
    assert chat[-1].get("role") == "user"
    assert chat[-1].get("content") == "<@U04KU9EAYNQ> who made that song popular?"


def test_save_chat_to_ddb(dynamodb_mock, chat):
    table_name = 'test_public_chats'
    ddb_id = "public_chat_id"
    chat_id = "T04L47VTW0Z-C04L47VUPMX-1677959194.104609"
    table = dynamodb_mock.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': ddb_id, 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': ddb_id, 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )
    response = lambda_handler.save_chat_to_ddb(table, ddb_id, chat_id, chat)
    assert response.get("ResponseMetadata").get("HTTPStatusCode") == 200
    assert lambda_handler.get_chat_from_ddb_item(lambda_handler.get_ddb_item(table, ddb_id, chat_id)) == chat


def test_get_private_chat_id(message_event_private):
    assert lambda_handler.get_private_chat_id(message_event_private) == "T04L47VTW0Z-C04L47VUPMX-U04NSB59LP9"


def test_get_email(slack_users_info_response):
    assert lambda_handler.get_email(slack_users_info_response) == "test.user@gmail.com"
    assert lambda_handler.get_email({}) is None


def test_get_slack_id(slack_users_info_response):
    assert lambda_handler.get_slack_id(slack_users_info_response) == 'U04KU2Y1AMS-T04L47VTW0Z'
    assert lambda_handler.get_slack_id({}) is None


@freeze_time('2020-09-01 1:45:01')
def test_get_timestamp():
    assert lambda_handler.get_timestamp() == 1598924701