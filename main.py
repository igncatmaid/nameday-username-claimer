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
RED = '\033[31m'

# Utility function for colored logs
def debug_log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    level_colors = {
        "INFO": BLUE,
        "SUCCESS": GREEN,
        "WARNING": YELLOW,
        "ERROR": RED
    }
    color = level_colors.get(level, RESET)
    print(f"{color}{timestamp} {level}: {message}{RESET}")
class MinecraftSniper:
    def __init__(self, config: ConfigType):
        self.webhook_url = config["webhook_url"]
        self.user_id = config["user_id"]
        self.username = config["username"]
        self.email = config["email"]
        self.password = config["password"]
        self.delay = config.get("delay", DEFAULT_DELAY)
        self.message_group_size = config.get("message_group_size", DEFAULT_MESSAGE_GROUP_SIZE)
        self.access_token = None
        self.batch_logs = []

        print(
            f" _____                                                _____ \n"
            f"( ___ )                                              ( ___ )\n"
            f" |   |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|   | \n"
            f" |   |{PINK}  ,---.          ,--.       ,--. ,---.          {RESET}|   | \n"
            f" |   |{PINK} '   .-' ,--,--, `--' ,---. `--'/  .-',--. ,--. {RESET}|   | \n"
            f" |   |{PINK} `.  `-. |      \\,--.| .-. |,--.|  `-, \\  '  /  {RESET}|   | \n"
            f" |   |{PINK} .-'    ||  ||  ||  || '-' '|  ||  .-'  \\   '   {RESET}|   | \n"
            f" |   |{PINK} `-----' `--''--'`--'|  |-' `--'`--'  .-'  /    {RESET}|   | \n"
            f" |   |{PINK}                     `--'             `---'     {RESET}|   | \n"
            f" |___|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|___| \n"
            f"(_____)                                              (_____)\n"
            f"{YELLOW}THIS CLAIMER IS ONLY FOR WHEN UNMIGRATED ACCOUNTS GET DELETED!{RESET}\n"
            f"The Minecraft Sniper script has started running!\n"
            f"Target Username: {self.username}\n"
            f"Delay between checks: {self.delay} seconds"
        )
        debug_log("The Minecraft Sniper script has started running!", "SUCCESS")
        debug_log(f"Target Username: {self.username}", "INFO")
        debug_log(f"Delay between checks: {self.delay} seconds", "INFO")
        self.send_discord_notification(
            embed=self.generate_embed(
                title="Script Started",
                description=f"Target Username: `{self.username}`\nDelay: `{self.delay} seconds`",
                color=0x6a0dad
            )
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

    def send_discord_notification(self, embed: Dict[str, Any] = None) -> None:
        payload = {"content": "", "embeds": [embed] if embed else []}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers=headers
            )
            if response.status_code != 204:
                debug_log(f"Failed to send notification: {response.status_code}, {response.text}", "ERROR")
        except requests.RequestException as e:
            debug_log(f"Error sending Discord notification: {e}", "ERROR")

    def generate_embed(self, title: str, description: str, color: int, timestamp: bool = True) -> Dict[str, Any]:
        embed = {
            "author": {
                "name": "Info",
                "icon_url": "https://avatars.githubusercontent.com/u/196719707?s=1000&v=4",
                "url": "https://github.com/snipify"
            },
            "title": title,
            "description": description,
            "color": color,
            "footer": {
                "text": "Namesnatcher - Minecraft Nameday Sniper",
            }
        }
        if timestamp:
            embed["timestamp"] = datetime.now().isoformat()
        return embed

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
        if self.access_token:
            return True  # Skip re-authentication if already authenticated

        auth_result = login(self.email, self.password)

        if isinstance(auth_result, dict):
            self.access_token = auth_result['access_token']
            embed = self.generate_embed(
                title="Authentication Success",
                description=(
                    f"Successfully authenticated with username `{auth_result['username']}`\n"
                    f"Bearer Token: ||`{auth_result['access_token']}`||\n"
                    f"UUID: `{auth_result['uuid']}`"
                ),
                color=0x00b0f4
            )
            debug_log(f"Authentication successful for username {self.username}", "SUCCESS")
            self.send_discord_notification(embed=embed)
            return True

        debug_log(f"Authentication failed for username {self.username}: {auth_result}", "ERROR")
        self.send_discord_notification(
            embed=self.generate_embed(
                title="Authentication Failed",
                description=f"Error: {auth_result}",
                color=0xff0000
            )
        )
        return False

    def claim_username(self) -> None:
        if not self.access_token:
            debug_log("Cannot claim username without authentication.", "ERROR")
            return

        url = f"{MINECRAFT_API_BASE}/minecraft/profile/name/{self.username}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
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

            embed = self.generate_embed(
                title="Claim Username",
                description=f"Attempt to claim `{self.username}`: {status}",
                color=0x6a0dad if response.status_code == 200 else 0xffa500
            )

            if response.status_code == 200:
                debug_log(f"Successfully claimed username {self.username}", "SUCCESS")
                self.send_discord_notification(embed=embed)

            # Using _handle_status for batch logging
            self._handle_status(
                datetime.now().strftime("%H:%M:%S"),
                status_messages.get(response.status_code, "Unexpected error"),
                "SUCCESS" if response.status_code == 200 else "WARNING",
                0x6a0dad if response.status_code == 200 else 0xffa500
            )

        except requests.RequestException as e:
            debug_log(f"Error claiming username {self.username}: {e}", "ERROR")
            self.send_discord_notification(
                embed=self.generate_embed(
                    title="Error Claiming Username",
                    description=f"Error: {e}",
                    color=0xff0000
                )
            )

    def _handle_status(self, timestamp: str, message: str, log_level: str, color: int) -> bool:
        debug_log(f"[{timestamp}] {message}", log_level)
        self.batch_logs.append(f"Attempt to claim {self.username}: {message}")

        if len(self.batch_logs) >= self.message_group_size:
            self.send_discord_notification(
                embed=self.generate_embed(
                    title="Batch Update",
                    description="\n".join(self.batch_logs),
                    color=color
                )
            )
            self.batch_logs.clear()
        return False

    def handle_taken_username(self, timestamp: str) -> bool:
        return self._handle_status(
            timestamp,
            "Username is taken.",
            "INFO",
            0xffa500
        )

    def handle_ratelimited(self, timestamp: str) -> bool:
        return self._handle_status(
            timestamp,
            "Rate limited by Mojang API. Please wait.",
            "WARNING",
            0xffa500
        )

    def handle_error(self, timestamp: str) -> bool:
        return self._handle_status(
            timestamp,
            "Error checking username.",
            "ERROR",
            0xff0000
        )

    def run(self) -> None:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            status = self.check_username_availability()

            status_handlers: Dict[str, StatusHandler] = {
                "ratelimited": lambda: self.handle_ratelimited(timestamp),
                "error": lambda: self.handle_error(timestamp),
                "available": lambda: self.authenticate_account() and self.claim_username(),
                "taken": lambda: self.handle_taken_username(timestamp)
            }

            status_handlers[status]()

            time.sleep(self.delay)

def main():
    try:
        config = MinecraftSniper.load_config()
        required_keys = ["webhook_url", "user_id", "username", "email", "password"]

        if not all(key in config for key in required_keys):
            debug_log(f"Error: Missing required configuration in {CONFIG_FILE}", "ERROR")
            return

        sniper = MinecraftSniper(config)
        sniper.run()
    except Exception as e:
        debug_log(f"Fatal error: {e}", "ERROR")

if __name__ == "__main__":
    main()
