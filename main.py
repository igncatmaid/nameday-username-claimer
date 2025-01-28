import time
import requests
import json
from datetime import datetime
from typing import Dict, Any, Callable
from MsAuth import login

# Constants
CONFIG_FILE = "config.json"
MOJANG_API_BASE = "https://api.mojang.com"
MINECRAFT_API_BASE = "https://api.minecraftservices.com"
DEFAULT_DELAY = 5
DEFAULT_MESSAGE_GROUP_SIZE = 3

# Type aliases
ConfigType = Dict[str, Any]
StatusHandler = Callable[[], bool]

# Define ANSI escape codes for colors ONLY FOR CONSOLE
RESET = '\033[0m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
PINK = '\033[1;35m'

class MinecraftSniper:
    def __init__(self, config: ConfigType):
        self.webhook_url = config["webhook_url"]
        self.user_id = config["user_id"]
        self.username = config["username"]
        self.email = config["email"]
        self.password = config["password"]
        self.delay = config.get("delay", DEFAULT_DELAY)
        self.message_group_size = config.get("message_group_size", DEFAULT_MESSAGE_GROUP_SIZE)
        self.count_taken = 0
        print(
            f" _____                                                _____ \n"
            f"( ___ )                                              ( ___ )\n"
            f" |   |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|   | \n"
            f" |   |{PINK}  ,---.          ,--.       ,--. ,---.          {RESET}|   | \n"
            f" |   |{PINK} '   .-' ,--,--, `--' ,---. `--'/  .-',--. ,--. {RESET}|   | \n"
            f" |   |{PINK} `.  `-. |      \,--.| .-. |,--.|  `-, \  '  /  {RESET}|   | \n"
            f" |   |{PINK} .-'    ||  ||  ||  || '-' '|  ||  .-'  \   '   {RESET}|   | \n"
            f" |   |{PINK} `-----' `--''--'`--'|  |-' `--'`--'  .-'  /    {RESET}|   | \n"
            f" |   |{PINK}                     `--'             `---'     {RESET}|   | \n"
            f" |___|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|___| \n"
            f"(_____)                                              (_____)\n"
            f"{YELLOW}THIS CLAIMER IS ONLY FOR WHEN UNMIGRATED ACCOUNTS GET DELETED!{RESET}\n"
            f"The Minecraft Sniper script has started running!\n"
            f"Target Username: {self.username}\n"
            f"Delay between checks: {self.delay} seconds"
        )
        self.send_discord_notification(
            f" ``` _____                                                _____ \n"
            f"( ___ )                                              ( ___ )\n"
            f" |   |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|   | \n"
            f" |   |  ,---.          ,--.       ,--. ,---.          |   | \n"
            f" |   | '   .-' ,--,--, `--' ,---. `--'/  .-',--. ,--. |   | \n"
            f" |   | `.  `-. |      \,--.| .-. |,--.|  `-, \  '  /  |   | \n"
            f" |   | .-'    ||  ||  ||  || '-' '|  ||  .-'  \   '   |   | \n"
            f" |   | `-----' `--''--'`--'|  |-' `--'`--'  .-'  /    |   | \n"
            f" |   |                     `--'             `---'     |   | \n"
            f" |___|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|___| \n"
            f"(_____)                                              (_____)```\n"
            f"**THIS CLAIMER IS ONLY FOR WHEN UNMIGRATED ACCOUNTS GET DELETED!**\n"
            f"<@{self.user_id}>\n"
            f"The Minecraft Sniper script has started running!\n"
            f"Target Username: `{self.username}`\n"
            f"Delay between checks: `{self.delay} seconds`"
        )


    @staticmethod
    def load_config() -> ConfigType:
        try:
            with open(CONFIG_FILE, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {CONFIG_FILE} not found")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in {CONFIG_FILE}")

    def send_discord_notification(self, message: str, mention_user: bool = False) -> None:
        if mention_user:
            message = f"<@{self.user_id}> {message}"

        payload = {"content": message}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers=headers
            )
            if response.status_code != 204:
                print(f"Failed to send notification: {response.status_code}, {response.text}")
        except requests.RequestException as e:
            print(f"Error sending Discord notification: {e}")

    def check_username_availability(self) -> str:
        url = f"{MOJANG_API_BASE}/users/profiles/minecraft/{self.username}"
        
        try:
            response = requests.get(url)
            status_map = {
                429: "ratelimited",
                204: "available",
                404: "available",
                200: "taken"
            }
            return status_map.get(response.status_code, "error")
        except requests.RequestException:
            return "error"

    def authenticate_account(self) -> bool:
        auth_result = login(self.email, self.password)
        
        if isinstance(auth_result, dict):
            message = (
                f"Successfully authenticated with username `{self.username}!`\n"
                f"Bearer Token: ||`{auth_result['access_token']}`||\n"
                f"Learn more: <https://bearer.wiki>\n"
                f"UUID: `{auth_result['uuid']}`"
            )
            print(
                f"Successfully authenticated with username {self.username}!\n"
                f"Bearer Token: {auth_result['access_token']}\n"
                f"Learn more: <https://bearer.wiki>\n"
                f"UUID: {auth_result['uuid']}"
            )
            self.send_discord_notification(message, mention_user=True)
            self.claim_username(auth_result['access_token'])
            return True
        
        error_message = f"Authentication failed for `{self.username}`: `{auth_result}`"
        self.send_discord_notification(error_message, mention_user=True)
        return False

    def claim_username(self, access_token: str) -> None:
        url = f"{MINECRAFT_API_BASE}/minecraft/profile/name/{self.username}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        status_messages = {
            200: "Successfully claimed",
            400: "Invalid request",
            401: "Unauthorized (invalid access token)",
            403: "Forbidden (username taken or cooldown)",
            404: "Account does not own Minecraft",
            405: "Method not allowed",
            429: "Rate limit exceeded",
            500: "Internal server error"
        }

        try:
            response = requests.put(url, headers=headers)
            status = status_messages.get(response.status_code, "Unexpected error")
            message = f"`{self.username}`: `{status}`"
            
            if response.status_code != 200:
                message = f"Failed to claim {message}"
            
            self.send_discord_notification(message, mention_user=True)
        except requests.RequestException as e:
            error_message = f"Error claiming username `{self.username}`: `{e}`"
            self.send_discord_notification(error_message, mention_user=True)

    def handle_taken_username(self, timestamp: str) -> bool:
        print(
            f"[{timestamp}] Username {self.username} is taken."
        )
        self.count_taken += 1
        if self.count_taken % self.message_group_size == 0:
            self.send_discord_notification(
                f"`[{timestamp}]` Username `{self.username}` is taken. `{self.count_taken}x`"
            )
            self.count_taken = 0
        return False

    def handle_ratelimited(self, timestamp: str) -> bool:
        print(
            f"[{timestamp}] Rate limited by Mojang API. Please wait."
        )
        self.send_discord_notification(
            f"`[{timestamp}]` Rate limited by Mojang API. Please wait.."
        )
        return False
    def handle_error(self, timestamp: str) -> bool:
        print(
            f"[{timestamp}] Error checking username {self.username}."
        )
        self.send_discord_notification(
            f"`[{timestamp}]` Error checking username `{self.username}`."
        )
        return False

    def run(self) -> None:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            status = self.check_username_availability()

            status_handlers: Dict[str, StatusHandler] = {
                "ratelimited": lambda: self.handle_ratelimited(timestamp),
                "error": lambda: self.handle_error(timestamp),
                "available": lambda: self.authenticate_account(),
                "taken": lambda: self.handle_taken_username(timestamp)
            }

            if status_handlers[status]():
                break

            time.sleep(self.delay)

def main():
    try:
        config = MinecraftSniper.load_config()
        required_keys = ["webhook_url", "user_id", "username", "email", "password"]
        
        if not all(key in config for key in required_keys):
            print(f"Error: Missing required configuration in {CONFIG_FILE}")
            return
        sniper = MinecraftSniper(config)
        sniper.run()
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
