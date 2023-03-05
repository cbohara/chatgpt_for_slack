import pytest
import boto3
from moto import mock_dynamodb


@pytest.fixture
def openai_response():
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "Thank you! How may I assist you today?",
                    "role": "assistant"
                }
            }
        ],
        "created": 1677963856,
        "id": "chatcmpl-6qTL6bMrSEtUjCRbM4f3AkcaGwbZW",
        "model": "gpt-3.5-turbo-0301",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 12,
            "prompt_tokens": 13,
            "total_tokens": 25
        }
    }

@pytest.fixture(scope='function')
def dynamodb_mock():
    with mock_dynamodb():
        yield boto3.resource('dynamodb')


@pytest.fixture(scope='function')
def chat():
	return [
        {"role": "system", "content": "You are a helpful assistant."}
    ]


@pytest.fixture(scope='function')
def private_chats_item(chat):
	private_chat_id = 'T04L47VTW0Z-D04P9B9CU4C-U04NSB59LP9'
	return {'private_chat_id': private_chat_id, 'chat': chat}


@pytest.fixture(scope='function')
def public_chats_item(chat):
	public_chat_id = "T04L47VTW0Z-C04L47VUPMX-1677959194.104609"
	return {'public_chat_id': public_chat_id, 'chat': chat}


@pytest.fixture(scope='function')
def app_mention_event_thread_exists():
      return {
		"thread_ts": "1677959194.104609",
		"channel": "C04L47VUPMX",
		"team": "T04L47VTW0Z",
		"ts": "1677959194.104609",
		"text": "<@U04KU9EAYNQ> who made that song popular?"
	  }


@pytest.fixture(scope='function')
def app_mention_event_thread_does_not_exist():
      return {
		"ts": "1677959194.104609",
		"channel": "C04L47VUPMX",
		"team": "T04L47VTW0Z",
		"text": "<@U04KU9EAYNQ> what does the fox say?"
	  }


@pytest.fixture(scope='function')
def message_event_private():
      return {
		"channel": "C04L47VUPMX",
		"team": "T04L47VTW0Z",
		"user": "U04NSB59LP9",
		"text": "Why did the chicken cross the road?",
		"channel_type": "im",
		"api_app_id":"A04LFFL3URE"
	  }


@pytest.fixture(scope='function')
def chat():
	return [
		{"role": "system", "content": "You are a helpful assistant."},
		{"role": "user", "content": "<@U04KU9EAYNQ> who made that song popular?"},
		{"role": "assistant", "content": "Diana Ross"}
	]