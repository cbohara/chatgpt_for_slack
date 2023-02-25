import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize a Slack API client
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

user_id = "U04KU9EAYNQ"
# Call the users.info API method to get information about the bot user
try:
    response = client.users_info(user=user_id)
    # Extract the username and display name from the response
    username = response["user"]["name"]
    display_name = response["user"]["profile"]["display_name"]
    # Use the username and/or display name to refer to the bot user in your code
    print(f"The bot user's name is {username} ({display_name})")
except SlackApiError as e:
    print(f"Error: {e}")
