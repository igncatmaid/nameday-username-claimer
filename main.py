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
    if response.status_code == 429:
        return "ratelimited"  # Indicate rate limiting
    elif response.status_code == 204 or response.status_code == 404:
        return True  # Username is available
    elif response.status_code == 200:
        return False  # Username is taken
    else:
        print(f"Unexpected response from API: {response.status_code}")
        return "error"

# Notify via Discord webhook
import requests
import json

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

    try:
        response = requests.put(url, headers=headers)
        
        if response.status_code == 200:
            message = f"Successfully claimed the username `{username}`!"
            print(message)
            send_discord_notification(webhook_url, user_id, message)
        elif response.status_code == 400:
            error_message = response.json().get("errorMessage", "Invalid request")
            if "size must be between" in error_message:
                message = f"Failed to claim the username `{username}`. Error: Invalid username length (3-16 characters)."
            elif "Invalid profile name" in error_message:
                message = f"Failed to claim the username `{username}`. Error: Invalid username format."
            else:
                message = f"Failed to claim the username `{username}`. Error: {error_message}"
            print(message)
            send_discord_notification(webhook_url, user_id, message)
        elif response.status_code == 401:
            message = f"Failed to claim the username `{username}`. Error: Unauthorized (invalid access token)."
            print(message)
            send_discord_notification(webhook_url, user_id, message)
        elif response.status_code == 403:
            message = f"Failed to claim the username `{username}`. Error: Forbidden (username already taken or cooldown period)."
            print(message)
            send_discord_notification(webhook_url, user_id, message)
        elif response.status_code == 404:
            message = f"Failed to claim the username `{username}`. Error: Account does not own Minecraft."
            print(message)
            send_discord_notification(webhook_url, user_id, message)
        elif response.status_code == 405:
            message = f"Failed to claim the username `{username}`. Error: Method not allowed (use PUT)."
            print(message)
            send_discord_notification(webhook_url, user_id, message)
        elif response.status_code == 429:
            message = f"Failed to claim the username `{username}`. Error: Too many requests (rate limit exceeded)."
            print(message)
            send_discord_notification(webhook_url, user_id, message)
        elif response.status_code == 500:
            message = f"Failed to claim the username `{username}`. Error: Internal server error."
            print(message)
            send_discord_notification(webhook_url, user_id, message)
        else:
            message = f"Failed to claim the username `{username}`. Error: Unexpected error (Status Code: {response.status_code})."
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

    while True:
        print(f"Checking availability for username: {username}")
        status = is_username_available(username)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Get current timestamp

        if status == "ratelimited":
            print("Rate limited by Mojang API.")
            send_discord_notification(webhook_url, f"`[{timestamp}]` Rate limited by Mojang API. Please wait before continuing.")
        elif status == "error":
            print(f"Error checking username: {username}.")
            send_discord_notification(webhook_url, f"`[{timestamp}]` Error occurred while checking the username `{username}`.")
        elif status:
            print(f"Username '{username}' is available!")
            send_discord_notification(webhook_url, user_id, f"`[{timestamp}]` The username `{username}` is available! Attempting authentication...")
            # Attempt authentication and stop if successful
            if authenticate_account(email, password, webhook_url, user_id, username):
                break  # Stop checking if authentication is successful
        else:
            print(f"Username '{username}' is taken.")
            count_taken += 1
            if count_taken % message_group_size == 0:  # Only send every nth "taken" message based on config
                send_discord_notification(webhook_url, f"`[{timestamp}]` The username `{username}` is already taken.`{count_taken}x`")
                count_taken = 0
    
        time.sleep(delay)

if __name__ == "__main__":
    main()
