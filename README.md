## Nameday Username Claimer

This script automates the process of checking the availability of a Minecraft username and claiming it when usernames are freed (on the day when unmigrated accounts are deleted).

⚠️ THIS ISNT REGULAR USERNAME CLAIMER, ITS ONLY FOR DAY WHEN UNMIGRATED ACCOUNT GET DELETED ⚠️

## Features

- Check if a Minecraft username is available.
- Authenticate using Microsoft credentials.
- Claim the username if it's available.
- Send notifications via Discord webhook on key events (successful authentication, rate limit, errors etc.).
- Configurable delay and message grouping for notifications.

## Requirements

- Python 3.7 or higher ( https://www.python.org/downloads/ )
- `requests` library (can be installed using `install.bat`)

## Installation

1. Clone or download this repository to your local machine.
2. Ensure you have Python 3.7 or higher installed.
3. Install the required libraries using `install.bat`
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
