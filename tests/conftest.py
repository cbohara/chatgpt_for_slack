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

@pytest.fixture(scope='function')
def slack_users_info_response():
    return {'ok': True, 'user': {'id': 'U04KU2Y1AMS', 'team_id': 'T04L47VTW0Z', 'name': 'test.user', 'deleted': False, 'color': '9f69e7', 'real_name': 'Charlie', 'tz': 'America/Los_Angeles', 'tz_label': 'Pacific Daylight Time', 'tz_offset': -25200, 'profile': {'title': '', 'phone': '', 'skype': '', 'real_name': 'Charlie', 'real_name_normalized': 'Charlie', 'display_name': '', 'display_name_normalized': '', 'fields': None, 'status_text': '', 'status_emoji': '', 'status_emoji_display_info': [], 'status_expiration': 0, 'avatar_hash': '22e44a86cf18', 'image_original': 'https://avatars.slack-edge.com/2023-01-19/4668689269509_22e44a86cf182c8b85eb_original.png', 'is_custom_image': True, 'email': 'test.user@gmail.com', 'first_name': 'Charlie', 'last_name': '', 'image_24': 'https://avatars.slack-edge.com/2023-01-19/4668689269509_22e44a86cf182c8b85eb_24.png', 'image_32': 'https://avatars.slack-edge.com/2023-01-19/4668689269509_22e44a86cf182c8b85eb_32.png', 'image_48': 'https://avatars.slack-edge.com/2023-01-19/4668689269509_22e44a86cf182c8b85eb_48.png', 'image_72': 'https://avatars.slack-edge.com/2023-01-19/4668689269509_22e44a86cf182c8b85eb_72.png', 'image_192': 'https://avatars.slack-edge.com/2023-01-19/4668689269509_22e44a86cf182c8b85eb_192.png', 'image_512': 'https://avatars.slack-edge.com/2023-01-19/4668689269509_22e44a86cf182c8b85eb_512.png', 'image_1024': 'https://avatars.slack-edge.com/2023-01-19/4668689269509_22e44a86cf182c8b85eb_1024.png', 'status_text_canonical': '', 'team': 'T04L47VTW0Z'}, 'is_admin': True, 'is_owner': True, 'is_primary_owner': True, 'is_restricted': False, 'is_ultra_restricted': False, 'is_bot': False, 'is_app_user': False, 'updated': 1676158294, 'is_email_confirmed': True, 'who_can_share_contact_card': 'EVERYONE'}}