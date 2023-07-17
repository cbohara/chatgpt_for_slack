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

@pytest.fixture(scope='function')
def slack_team_info_response():
    pass


@pytest.fixture(scope='function')
def app_home_opened_event_minimum():
      return {'type': 'app_home_opened', 'user': 'U04PWB6MARE', 'channel': 'D059KA7TQLX', 'tab': 'messages', 'event_ts': '1688408768.212345'}

@pytest.fixture(scope='function')
def app_home_opened_event():
    return {'type': 'app_home_opened', 'user': 'U04PWB6MARE', 'channel': 'D059KA7TQLX', 'tab': 'home', 'view': {'id': 'V05FJKQH5ED', 'team_id': 'T04P94U7N2Y', 'type': 'home', 'blocks': [{'type': 'section', 'block_id': '6mM', 'text': {'type': 'mrkdwn', 'text': ":wave: Hi! I'm Bounce, your ChatGPT for Slack app!", 'verbatim': False}}, {'type': 'section', 'block_id': 'am0', 'text': {'type': 'mrkdwn', 'text': 'We hope you are enjoying your free trial!', 'verbatim': False}}, {'type': 'section', 'block_id': '=UP', 'text': {'type': 'mrkdwn', 'text': 'Click one of the buttons below to start your subscription!', 'verbatim': False}}, {'type': 'actions', 'block_id': 'vuxD', 'elements': [{'type': 'button', 'action_id': 'M0Wg', 'text': {'type': 'plain_text', 'text': 'Lifetime access for only $100', 'emoji': True}, 'url': 'https://buy.stripe.com/14kg1k9Ld57x1naeUW'}]}, {'type': 'actions', 'block_id': 'tM8D1', 'elements': [{'type': 'button', 'action_id': 'cAfv', 'text': {'type': 'plain_text', 'text': 'Annual access for $50/year', 'emoji': True}, 'url': 'https://buy.stripe.com/8wM2aue1t57xd5S4gh'}]}, {'type': 'actions', 'block_id': '+HqlK', 'elements': [{'type': 'button', 'action_id': 'efpHq', 'text': {'type': 'plain_text', 'text': 'Monthly access for $5/month', 'emoji': True}, 'url': 'https://buy.stripe.com/8wM8yS4qT9nNgi44gg'}]}], 'private_metadata': '', 'callback_id': 'home_view', 'state': {'values': {}}, 'hash': '1688407371.DPKueFja', 'title': {'type': 'plain_text', 'text': 'View Title', 'emoji': True}, 'clear_on_close': False, 'notify_on_close': False, 'close': None, 'submit': None, 'previous_view_id': None, 'root_view_id': 'V05FJKQH5ED', 'app_id': 'A04UK4S6W4R', 'external_id': '', 'app_installed_team_id': 'T04P94U7N2Y', 'bot_id': 'B059ZNCK1R9'}, 'event_ts': '1688408770.726983'}

@pytest.fixture(scope='function')
def message_event():
      return {'client_msg_id': '9bfeda91-8677-4644-ba91-ef4fdbfbaf62', 'type': 'message', 'text': 'what are some fun things to do in the summer in san diego?', 'user': 'U04KU2Y1AMS', 'ts': '1688408791.468069', 'blocks': [{'type': 'rich_text', 'block_id': 'DYB4', 'elements': [{'type': 'rich_text_section', 'elements': [{'type': 'text', 'text': 'what are some fun things to do in the summer in san diego?'}]}]}], 'team': 'T04L47VTW0Z', 'channel': 'D04U9091QJG', 'event_ts': '1688408791.468069', 'channel_type': 'im'}


@pytest.fixture(scope='function')
def app_mention_event():
    return {'client_msg_id': '410180f9-3aab-4a2d-bd7a-39582cbb7a4e', 'type': 'app_mention', 'text': '<@U05APH92U4Q> where are great places to travel in the world in july?', 'user': 'U04PWB6MARE', 'ts': '1688409244.909969', 'blocks': [{'type': 'rich_text', 'block_id': 'aCN', 'elements': [{'type': 'rich_text_section', 'elements': [{'type': 'user', 'user_id': 'U05APH92U4Q'}, {'type': 'text', 'text': ' where are great places to travel in the world in july?'}]}]}], 'team': 'T04P94U7N2Y', 'channel': 'C04PK9RLD6V', 'event_ts': '1688409244.909969'}


@pytest.fixture(scope='function')
def stripe_payment_intent_succeeded_event():
    return '''{
    "id": "evt_3NTtGyHedDKL853p1BodDrFU",
    "object": "event",
    "api_version": "2020-08-27",
    "created": 1689369093,
    "data": {
        "object": {
        "id": "pi_3NTtGyHedDKL853p1HdWLonB",
        "object": "payment_intent",
        "amount": 50,
        "amount_capturable": 0,
        "amount_details": {
            "tip": {
            }
        },
        "amount_received": 50,
        "application": null,
        "application_fee_amount": null,
        "automatic_payment_methods": null,
        "canceled_at": null,
        "cancellation_reason": null,
        "capture_method": "automatic",
        "charges": {
            "object": "list",
            "data": [
            {
                "id": "ch_3NTtGyHedDKL853p1CAQ9kLK",
                "object": "charge",
                "amount": 50,
                "amount_captured": 50,
                "amount_refunded": 0,
                "application": null,
                "application_fee": null,
                "application_fee_amount": null,
                "balance_transaction": "txn_3NTtGyHedDKL853p1pizkmX2",
                "billing_details": {
                "address": {
                    "city": null,
                    "country": "US",
                    "line1": null,
                    "line2": null,
                    "postal_code": "92116",
                    "state": null
                },
                "email": "lol@lol.com",
                "name": "Test",
                "phone": null
                },
                "calculated_statement_descriptor": "MEDIUM.COM",
                "captured": true,
                "created": 1689369093,
                "currency": "usd",
                "customer": null,
                "description": null,
                "destination": null,
                "dispute": null,
                "disputed": false,
                "failure_balance_transaction": null,
                "failure_code": null,
                "failure_message": null,
                "fraud_details": {
                },
                "invoice": null,
                "livemode": false,
                "metadata": {
                },
                "on_behalf_of": null,
                "order": null,
                "outcome": {
                "network_status": "approved_by_network",
                "reason": null,
                "risk_level": "normal",
                "risk_score": 49,
                "seller_message": "Payment complete.",
                "type": "authorized"
                },
                "paid": true,
                "payment_intent": "pi_3NTtGyHedDKL853p1HdWLonB",
                "payment_method": "pm_1NTtGyHedDKL853pU6Ipzxh1",
                "payment_method_details": {
                "card": {
                    "brand": "visa",
                    "checks": {
                    "address_line1_check": null,
                    "address_postal_code_check": "pass",
                    "cvc_check": "pass"
                    },
                    "country": "US",
                    "exp_month": 1,
                    "exp_year": 2027,
                    "fingerprint": "thsI0J7hfApLMnKm",
                    "funding": "credit",
                    "installments": null,
                    "last4": "4242",
                    "mandate": null,
                    "network": "visa",
                    "network_token": {
                    "used": false
                    },
                    "three_d_secure": null,
                    "wallet": {
                    "dynamic_last4": null,
                    "link": {
                    },
                    "type": "link"
                    }
                },
                "type": "card"
                },
                "receipt_email": null,
                "receipt_number": null,
                "receipt_url": "https://pay.stripe.com/receipts/payment/CAcaFwoVYWNjdF8xSUg5MlZIZWRES0w4NTNwKIb0xqUGMgZwbtGPgDE6LBakgfs11wrl2KyaFaEf8dXsHkTRoJ4UKixa0lReDUlFeuEnP77qdFHarTuX",
                "refunded": false,
                "refunds": {
                "object": "list",
                "data": [
                ],
                "has_more": false,
                "total_count": 0,
                "url": "/v1/charges/ch_3NTtGyHedDKL853p1CAQ9kLK/refunds"
                },
                "review": null,
                "shipping": null,
                "source": null,
                "source_transfer": null,
                "statement_descriptor": null,
                "statement_descriptor_suffix": null,
                "status": "succeeded",
                "transfer_data": null,
                "transfer_group": null
            }
            ],
            "has_more": false,
            "total_count": 1,
            "url": "/v1/charges?payment_intent=pi_3NTtGyHedDKL853p1HdWLonB"
        },
        "client_secret": "pi_3NTtGyHedDKL853p1HdWLonB_secret_yerkKwtngqhPzxwKb4xkYb2S3",
        "confirmation_method": "automatic",
        "created": 1689369092,
        "currency": "usd",
        "customer": null,
        "description": null,
        "invoice": null,
        "last_payment_error": null,
        "latest_charge": "ch_3NTtGyHedDKL853p1CAQ9kLK",
        "livemode": false,
        "metadata": {
        },
        "next_action": null,
        "on_behalf_of": null,
        "payment_method": "pm_1NTtGyHedDKL853pU6Ipzxh1",
        "payment_method_options": {
            "card": {
            "installments": null,
            "mandate_options": null,
            "network": null,
            "request_three_d_secure": "automatic"
            }
        },
        "payment_method_types": [
            "card"
        ],
        "processing": null,
        "receipt_email": null,
        "review": null,
        "setup_future_usage": null,
        "shipping": null,
        "source": null,
        "statement_descriptor": null,
        "statement_descriptor_suffix": null,
        "status": "succeeded",
        "transfer_data": null,
        "transfer_group": null
        }
    },
    "livemode": false,
    "pending_webhooks": 1,
    "request": {
        "id": "req_MgItVLYxYi32VM",
        "idempotency_key": "3a3cf1f0-54e3-46f6-b228-2ad7ee5c14d4"
    },
    "type": "payment_intent.succeeded"
    }'''