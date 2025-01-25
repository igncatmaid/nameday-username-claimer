# Minecraft Username Claim Script

This script is intended for the day when unmigrated accounts are deleted and usernames are freed.
This script automates the process of checking the availability of a Minecraft username and Claiming it.

## Features
- Check if a Minecraft username is available.
- Authenticate using Microsoft credentials (requires the `MsAuth` module).
- Claim the username if it's available.
- Send notifications via Discord webhook on key events (e.g., successful authentication, rate limit, or errors).
- Configurable delay and message grouping for notifications.

## Requirements
- Python 3.7 or higher
- `requests` library (can be installed via `pip install requests`)

## Installation

1. Clone or download this repository to your local machine.
2. Ensure you have Python 3.7 or higher installed.
3. Install the required libraries using pip:
    ```bash
    pip install requests
    ```
4. Configure your settings in the `config.json` file (details below).

## Configuration

Create or update the `config.json` file with the following content:
```json
{
  "webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
  "user_id": "YOUR_DISCORD_USER_ID",
  "username": "desired_minecraft_username",
  "email": "your_microsoft_email",
  "password": "your_microsoft_password",
  "delay": 5,
  "message_group_size": 3
}
