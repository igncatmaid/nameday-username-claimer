import time
import requests
import json
from MsAuth import login  # Importing the login function from MsAuth.py
from datetime import datetime


# Load configuration from a file
CONFIG_FILE = "config.json"
def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

# Check username availability
def is_username_available(username):
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    response = requests.get(url)
    
    status_map = {
        429: "ratelimited",
        204: True,
        404: True,
        200: False
    }
    
    return status_map.get(response.status_code, "error")

def send_discord_notification(webhook_url, message, user_id=None):
    if user_id:
        message = f"<@{user_id}> {message}"
    
    payload = {
        "content": message,
    }
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
    if response.status_code == 204:
        print(f"Successfully sent notification: {message}")
    else:
        print(f"Failed to send notification: {response.status_code}, {response.text}")


# Attempt authentication using the custom login
def authenticate_account(email, password, webhook_url, user_id, username):
    auth_result = login(email, password)  # Call the login function from MsAuth.py
    
    if isinstance(auth_result, dict):  # Successful login
        message = (
            f"Successfully authenticated with username `{username}`!\n"
            f"Bearer Token (Access Token): `{auth_result['access_token']}`\n"
            f"Learn more about Minecraft Bearer Tokens here: <https://bearer.wiki>\n"
            f"UUID: `{auth_result['uuid']}`"
        )
        print(message)
        send_discord_notification(webhook_url, user_id, message)
        # Proceed to claim the username
        claim_username(username, auth_result['access_token'], webhook_url, user_id)
        return True  # Authentication successful, stop the loop
    else:
        message = f"Authentication failed for `{username}`: {auth_result}"
        print(message)
        send_discord_notification(webhook_url, user_id, message)
        return False  # Authentication failed

# Claim the username using the access token
# Modify the claim_username function to log the response body
def claim_username(username, access_token, webhook_url, user_id):
    url = 'https://api.minecraftservices.com/minecraft/profile/name/' + username
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    status_messages = {
        200: lambda: f"Successfully claimed the username `{username}`!",
        400: lambda: f"Failed to claim the username `{username}`. Error: {response.json().get('errorMessage', 'Invalid request')}",
        401: lambda: f"Failed to claim the username `{username}`. Error: Unauthorized (invalid access token).",
        403: lambda: f"Failed to claim the username `{username}`. Error: Forbidden (username already taken or cooldown period).",
        404: lambda: f"Failed to claim the username `{username}`. Error: Account does not own Minecraft.",
        405: lambda: f"Failed to claim the username `{username}`. Error: Method not allowed (use PUT).",
        429: lambda: f"Failed to claim the username `{username}`. Error: Too many requests (rate limit exceeded).",
        500: lambda: f"Failed to claim the username `{username}`. Error: Internal server error."
    }

    try:
        response = requests.put(url, headers=headers)
        message = status_messages.get(
            response.status_code,
            lambda: f"Failed to claim the username `{username}`. Error: Unexpected error (Status Code: {response.status_code})."
        )()
        print(message)
        send_discord_notification(webhook_url, user_id, message)
    except requests.exceptions.RequestException as error:
        message = f"Error claiming username `{username}`: {error}"
        print(message)
        send_discord_notification(webhook_url, user_id, message)


# Main function
def main():
    config = load_config()

    webhook_url = config.get("webhook_url")
    user_id = config.get("user_id")
    username = config.get("username")
    email = config.get("email")
    password = config.get("password")
    delay = config.get("delay", 5)  # Default delay of 5 seconds
    message_group_size = config.get("message_group_size", 3)  # Default message group size of 3

    if not webhook_url or not user_id or not username or not email or not password or not message_group_size:
        print("Error: Missing required configuration in config.json")
        return

    count_taken = 0
    status_handlers = {
        "ratelimited": lambda: send_discord_notification(webhook_url, f"`[{timestamp}]` Rate limited by Mojang API. Please wait before continuing."),
        "error": lambda: send_discord_notification(webhook_url, f"`[{timestamp}]` Error occurred while checking the username `{username}`."),
        True: lambda: authenticate_and_break(email, password, webhook_url, user_id, username),
        False: lambda: handle_taken_username(count_taken, message_group_size, webhook_url, username, timestamp)
    }

    def authenticate_and_break(email, password, webhook_url, user_id, username):
        send_discord_notification(webhook_url, user_id, f"`[{timestamp}]` The username `{username}` is available! Attempting authentication...")
        return authenticate_account(email, password, webhook_url, user_id, username)

    def handle_taken_username(count, group_size, webhook_url, username, timestamp):
        nonlocal count_taken
        count_taken += 1
        if count_taken % group_size == 0:
            send_discord_notification(webhook_url, f"`[{timestamp}]` The username `{username}` is already taken.`{count_taken}x`")
            count_taken = 0
        return False

    while True:
        print(f"Checking availability for username: {username}")
        status = is_username_available(username)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if status_handlers[status]():
            break

        time.sleep(delay)

if __name__ == "__main__":
    main()
